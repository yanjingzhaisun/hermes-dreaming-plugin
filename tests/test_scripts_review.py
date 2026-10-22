"""Isolated regressions for the portable nightly scripts; no Hermes required."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import fact_extract_state as state
import fact_extract_sweep as sweep


def load_pending():
    approval = types.ModuleType('tools.write_approval')
    approval.MEMORY = 'memory'
    approval.list_pending = Mock(return_value=[])
    approval.discard_pending = Mock(return_value=True)
    memory = types.ModuleType('tools.memory_tool')
    memory.load_on_disk_store = Mock()
    memory.apply_memory_pending = Mock(return_value={'success': False, 'error': 'refused'})
    memory.destructive_ops = lambda payload: [payload]
    package = types.ModuleType('tools')
    package.write_approval = approval
    spec = importlib.util.spec_from_file_location('pending_review_test', ROOT / 'scripts/memory_pending_review.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'tools': package, 'tools.write_approval': approval,
                                  'tools.memory_tool': memory}):
        spec.loader.exec_module(module)
    return module


class ScratchTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='script-review-', dir=ROOT / 'tests')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)


class SourceLedger(ScratchTest):
    def test_dry_receipt_does_not_create_files(self):
        receipt = state.RunReceipt(self.root / 'runs', {}, dry_run=True)
        receipt.finish('completed')
        self.assertEqual(list(self.root.iterdir()), [])

    def test_generator_sources_are_consumed_and_replay_is_idempotent(self):
        extract = Mock(return_value=[{'content': 'fact'}])
        write = Mock(return_value=(1, True))
        for expected in (1, 0):
            result = state.consume_sources(self.root, 'session', state.source_chunks([(1, 'user', 'source')]),
                                           extract, lambda facts, transcript: facts, write)
            self.assertEqual(result['processed'], expected)
        extract.assert_called_once()
        write.assert_called_once()

    def test_invalid_chunk_sizes_fail_instead_of_dropping_text(self):
        for size in (-1, 0, 99, 100):
            with self.subTest(size=size), self.assertRaises(ValueError):
                list(state.source_chunks([(1, 'user', 'source')], size))


class PendingReview(ScratchTest):
    def setUp(self):
        super().setUp()
        self.module = load_pending()
        self.module.PENDING_DIR = self.root / 'pending'
        self.module.LOCK = self.module.PENDING_DIR / '.review.lock'
        self.module.RECEIPTS = self.root / 'receipts.jsonl'
        self.module.MEMORIES_DIR = self.root / 'memories'

    def invoke(self, *args):
        with patch.object(sys, 'argv', ['review', *args]), contextlib.redirect_stdout(io.StringIO()):
            return self.module.main()

    def test_dry_discard_does_not_mutate(self):
        self.invoke('--dry', '--discard', 'one', '--reason', 'test')
        self.module.wa.discard_pending.assert_not_called()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_dry_approve_does_not_load_store_or_create_files(self):
        self.invoke('--dry', '--approve', 'one')
        self.module.load_on_disk_store.assert_not_called()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_refusal_is_nonzero(self):
        with patch.object(self.module, '_load_record', return_value={'payload': {}}):
            self.assertEqual(self.invoke('--approve', 'one'), 1)

    def test_record_id_cannot_traverse_out_of_queue(self):
        (self.root / 'secret.json').write_text('{"payload": {}}')
        self.module.PENDING_DIR.mkdir()
        with self.assertRaises(ValueError):
            self.module._load_record('../secret')

    def test_unreadable_memory_is_not_reported_as_dead_pins(self):
        with patch.object(Path, 'read_text', side_effect=PermissionError('injected')):
            with self.assertRaises(PermissionError):
                self.module._file_text('memory')

    def test_full_pins_targets_and_content_are_used_for_review(self):
        prefix = 'x' * 120
        records = [
            {'id': 'a', 'payload': {'matched_entry': prefix + 'a', 'content': 'y' * 250}},
            {'id': 'b', 'payload': {'matched_entry': prefix + 'b'}},
            {'id': 'c', 'payload': {'target': 'user', 'matched_entry': prefix + 'a'}},
            {'id': 'd', 'payload': {'matched_entry': prefix + 'a'}},
            {'id': 'e', 'payload': {'action': 'batch', 'target': 'memory', 'operations': [
                {'target': 'user', 'matched_entry': 'user pin'}]}},
        ]
        self.module.wa.list_pending.return_value = records
        output = io.StringIO()
        with patch.object(self.module, '_file_text', side_effect=lambda target: 'user pin' if target == 'user' else prefix + 'a'), contextlib.redirect_stdout(output):
            self.module.cmd_list()
        rows = json.loads(output.getvalue())['records']
        self.assertEqual(rows[0]['dup_group'], ['a', 'd'])
        self.assertIsNone(rows[1]['dup_group'])
        self.assertIsNone(rows[2]['dup_group'])
        self.assertEqual(rows[0]['ops'][0]['content'], 'y' * 250)
        self.assertEqual(rows[0]['ops'][0]['matched_entry'], prefix + 'a')
        self.assertTrue(rows[4]['ops'][0]['pin_alive'])

    def test_partial_or_ambiguous_entry_is_not_a_live_pin(self):
        self.assertFalse(self.module._op_view({'matched_entry': 'pin'}, 'pin changed')['pin_alive'])
        self.assertFalse(self.module._op_view({'matched_entry': 'pin'}, 'pin\n§\npin')['pin_alive'])


class ProtectedCheck(ScratchTest):
    def run_check(self, text, expected):
        memories = self.root / 'memories'
        memories.mkdir(exist_ok=True)
        (memories / 'MEMORY.md').write_bytes(text.encode())
        (memories / 'USER.md').write_text('')
        source = (ROOT / 'scripts/dream_protected_check.py').read_text()
        source = source.replace('EXPECTED = {"MEMORY.md": {}, "USER.md": {}}', 'EXPECTED = ' + repr(expected))
        output = io.StringIO()
        namespace = {'__name__': '__main__'}
        code = 0
        with patch.dict('os.environ', {'HERMES_HOME': str(self.root)}), contextlib.redirect_stdout(output):
            try:
                exec(compile(source, 'dream_protected_check.py', 'exec'), namespace)
            except SystemExit as exc:
                code = exc.code
        return code, json.loads(output.getvalue())

    def test_reordered_and_changed_blocks_fail(self):
        blocks = {'first': (hashlib.sha256(b'first').hexdigest(), 'first'),
                  'second': (hashlib.sha256(b'second').hexdigest(), 'second')}
        expected = {'MEMORY.md': blocks, 'USER.md': {}}
        self.assertEqual(self.run_check('first\n§\nsecond', expected)[0], 0)
        self.assertNotEqual(self.run_check('second\n§\nfirst', expected)[0], 0)
        self.assertNotEqual(self.run_check('first changed\n§\nsecond', expected)[0], 0)

    def test_line_ending_changes_are_detected(self):
        expected = {'MEMORY.md': {'one': (hashlib.sha256(b'first\nline').hexdigest(), 'first')}, 'USER.md': {}}
        self.assertNotEqual(self.run_check('first\r\nline', expected)[0], 0)

    def test_full_labels_distinguish_blocks_and_duplicate_matches_fail(self):
        first, second = 'shared-prefix-first', 'shared-prefix-second'
        expected = {'MEMORY.md': {'one': (hashlib.sha256(first.encode()).hexdigest(), first),
                                  'two': (hashlib.sha256(second.encode()).hexdigest(), second)}, 'USER.md': {}}
        self.assertEqual(self.run_check(first + '\n§\n' + second, expected)[0], 0)
        code, output = self.run_check(first + '\n§\n' + first + '\n§\n' + second, expected)
        self.assertNotEqual(code, 0)
        self.assertEqual(output['MEMORY.md'][0]['status'], 'AMBIGUOUS')


class Sweep(ScratchTest):
    def test_main_missing_extractor_finishes_receipt_without_review_writes(self):
        with patch.object(sweep, 'HERMES_HOME', self.root), patch.object(sweep, 'JOURNAL', self.root / 'journal'), patch.object(sweep, 'soft_review_after_core') as review, patch.object(sys, 'argv', ['sweep']):
            self.assertEqual(sweep.main(), 0)
        review.assert_not_called()
        receipt = json.loads(next((self.root / 'journal/runs').glob('*.json')).read_text())
        self.assertEqual(receipt['status'], 'completed')
        self.assertEqual(receipt['skipped_reason'], {'extractor_unavailable': 1})

    def test_nonfinite_slice_sizes_are_rejected_before_writes(self):
        for value in ('nan', 'inf'):
            with self.subTest(value=value), patch.object(sys, 'argv', ['sweep', '--slice-hours', value]), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    sweep.main()
                self.assertEqual(error.exception.code, 2)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_main_dry_run_leaves_state_and_files_unchanged(self):
        db = self.root / 'state.db'
        with sqlite3.connect(db) as conn:
            conn.executescript('CREATE TABLE sessions(id TEXT,source TEXT); CREATE TABLE messages(id INTEGER,session_id TEXT,role TEXT,content TEXT,timestamp REAL,active INTEGER);')
        original = db.read_bytes()
        with patch.object(sweep, 'STATE_DB', db), patch.object(sweep, 'JOURNAL', self.root / 'journal'), patch.object(sys, 'argv', ['sweep', '--dry-run']):
            self.assertEqual(sweep.main(), 0)
        self.assertEqual(db.read_bytes(), original)
        self.assertEqual(list(self.root.iterdir()), [db])

    def test_sqlite_uri_handles_special_characters(self):
        db = self.root / 'state?#.db'
        with sqlite3.connect(db) as conn:
            conn.execute('CREATE TABLE marker(value)')
        receipt = state.RunReceipt(self.root / 'runs', {})
        with patch.object(sweep, 'STATE_DB', db), patch.object(sweep, '_run_locked', side_effect=lambda args, start, end, receipt, conn: conn.execute('SELECT count(*) FROM marker').fetchone()[0]):
            self.assertEqual(sweep.run_sweep(types.SimpleNamespace(dry_run=True), 0, 100, receipt), 0)

    def test_missing_extractor_is_documented_noop(self):
        receipt = state.RunReceipt(self.root / 'runs', {})
        args = types.SimpleNamespace(dry_run=False)
        with patch.object(sweep, 'HERMES_HOME', self.root), patch.object(sweep, 'STATE_DB', self.root / 'absent.db'):
            self.assertEqual(sweep.run_sweep(args, 0, 100, receipt), 0)
        self.assertEqual(receipt.data['skipped_reason'].get('extractor_unavailable'), 1)

    def test_soft_review_import_failure_is_recorded(self):
        receipt = state.RunReceipt(self.root / 'runs', {})
        with patch.dict(sys.modules, {'fact_semantic_review': None}):
            sweep.soft_review_after_core(types.SimpleNamespace(), receipt)
        self.assertEqual(receipt.data['soft_review']['status'], 'disabled')

    def test_historical_replay_ignores_later_cursor_and_slices(self):
        conn = sqlite3.connect(':memory:')
        self.addCleanup(conn.close)
        conn.executescript("CREATE TABLE sessions(id TEXT, source TEXT); CREATE TABLE messages(id INTEGER,session_id TEXT,role TEXT,content TEXT,timestamp REAL,active INTEGER); INSERT INTO sessions VALUES('s','api_server');")
        conn.executemany('INSERT INTO messages VALUES (?,\'s\',\'user\',\'source\',?,1)',
                         [(i, 100 + i) for i in range(1, 7)] + [(i, 4000 + i) for i in range(7, 13)])
        journal = self.root / 'journal'
        journal.mkdir()
        progress_path = journal / (hashlib.sha256(b's').hexdigest() + '.json')
        state.atomic_json(progress_path, {'session_id': 's', 'last_id': 100})
        process = Mock(return_value={'already_consumed': 0, 'legacy_held': 0, 'pending': 0})
        extractor = types.SimpleNamespace(load_env=lambda: {}, provider_chain_labels=lambda env: [],
            SHARED_ROOT=self.root / 'shared', LEGACY_SWEEP=self.root / 'legacy', process_sources=process,
            ProviderExhausted=type('ProviderExhausted', (Exception,), {}), drain_attempts=lambda: [], log=lambda text: None)
        spec = types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda module: None))
        deps = {'dream_corrections': types.SimpleNamespace(capture_since=lambda *args, **kwargs: {}),
                'factstore_v2_common': types.SimpleNamespace(connect=lambda path: sqlite3.connect(':memory:'), has_v2=lambda conn: False)}
        args = types.SimpleNamespace(dry_run=False, since=0, slice_hours=1)
        receipt = state.RunReceipt(journal / 'runs', {})
        with patch.object(sweep, 'JOURNAL', journal), patch.object(sweep, 'STATE_DB', self.root / 'state.db'), patch.dict(sys.modules, deps), patch.object(sweep.importlib.util, 'spec_from_file_location', return_value=spec), patch.object(sweep.importlib.util, 'module_from_spec', return_value=extractor):
            self.assertEqual(sweep._run_locked(args, 0, 10000, receipt, conn), 0)
        process.assert_called_once()
        self.assertEqual(len(process.call_args.args[1]), 2)
        self.assertEqual(json.loads(progress_path.read_text())['last_id'], 100)


if __name__ == '__main__':
    unittest.main()
