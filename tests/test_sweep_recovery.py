"""Offline sweep recovery regressions using the real shared source ledger."""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import fact_extract_state as state
import fact_extract_sweep as sweep


class SweepFixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='sweep-recovery-', dir=ROOT / 'tests')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.journal = self.root / 'journal'
        self.conn = sqlite3.connect(':memory:')
        self.addCleanup(self.conn.close)
        self.conn.executescript("""
            CREATE TABLE sessions(id TEXT, source TEXT);
            CREATE TABLE messages(id INTEGER, session_id TEXT, role TEXT,
                                  content TEXT, timestamp REAL, active INTEGER);
            INSERT INTO sessions VALUES ('s', 'api_server');
        """)
        self.written = []

        def write(fact):
            self.written.append(fact['content'])
            return len(self.written), True

        def process_sources(sid, chunks, env, *, rows, on_progress):
            return state.consume_sources(
                self.root / 'shared', sid, chunks,
                lambda transcript: [{'content': transcript}],
                lambda facts, transcript: facts, write, on_progress=on_progress)

        self.extractor = types.SimpleNamespace(
            load_env=lambda: {}, provider_chain_labels=lambda env: [],
            SHARED_ROOT=self.root / 'shared', LEGACY_SWEEP=self.root / 'legacy',
            process_sources=process_sources,
            ProviderExhausted=type('ProviderExhausted', (Exception,), {}),
            drain_attempts=lambda: [], log=lambda text: None)
        spec = types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda module: None))
        deps = {
            'dream_corrections': types.SimpleNamespace(capture_since=lambda *args, **kwargs: {}),
            'factstore_v2_common': types.SimpleNamespace(
                connect=lambda path: sqlite3.connect(':memory:'), has_v2=lambda conn: False),
        }
        for guard in (
            patch.object(sweep, 'JOURNAL', self.journal),
            patch.object(sweep, 'STATE_DB', self.root / 'state.db'),
            patch.object(sweep, 'STORE_DB', self.root / 'memory_store.db'),
            patch.dict(sys.modules, deps),
            patch.object(sweep.importlib.util, 'spec_from_file_location', return_value=spec),
            patch.object(sweep.importlib.util, 'module_from_spec', return_value=self.extractor),
        ):
            guard.start()
            self.addCleanup(guard.stop)

    def add_messages(self, first_id, first_timestamp):
        self.conn.executemany(
            "INSERT INTO messages VALUES (?, 's', 'user', ?, ?, 1)",
            [(first_id + i, f'source {first_id + i}', first_timestamp + i) for i in range(6)])

    def run_sweep(self, start, end, *, historical=False):
        args = types.SimpleNamespace(dry_run=False, since=start if historical else None,
                                     slice_hours=24)
        receipt = state.RunReceipt(self.journal / 'runs', {})
        code = sweep._run_locked(args, start, end, receipt, self.conn)
        return code, receipt

    def consumed_ids(self):
        path = state.session_path(self.root / 'shared', 's')
        if not path.exists():
            return set()
        return {item['id'] for unit in json.loads(path.read_text())['units']
                if unit['status'] == 'done' for item in unit['source']}


class SweepRecovery(SweepFixture):
    def test_historical_replay_does_not_skip_older_unconsumed_messages(self):
        self.add_messages(1, 10)
        self.add_messages(7, 100)
        self.assertEqual(self.run_sweep(99, 200, historical=True)[0], 0)
        self.assertEqual(self.consumed_ids(), set(range(7, 13)))
        self.assertEqual(self.run_sweep(99, 200)[0], 0)
        self.assertEqual(self.consumed_ids(), set(range(1, 13)))
        writes = list(self.written)
        self.assertEqual(self.run_sweep(99, 200)[0], 0)
        self.assertEqual(self.written, writes)

    def test_resumed_historical_replay_preserves_ordinary_cursor(self):
        self.add_messages(1, 10)
        self.add_messages(7, 100)
        with patch.object(self.extractor, 'process_sources',
                          side_effect=self.extractor.ProviderExhausted('injected outage')):
            self.assertEqual(self.run_sweep(99, 200, historical=True)[0], 1)
        self.assertEqual(self.run_sweep(99, 200, historical=True)[0], 0)
        self.assertEqual(self.run_sweep(99, 200)[0], 0)
        self.assertEqual(self.consumed_ids(), set(range(1, 13)))

    def test_default_resume_of_historical_plan_preserves_unconsumed_messages(self):
        self.add_messages(1, 10)
        self.add_messages(7, 100)
        with patch.object(self.extractor, 'process_sources',
                          side_effect=self.extractor.ProviderExhausted('injected outage')):
            self.assertEqual(self.run_sweep(99, 200, historical=True)[0], 1)
        self.assertEqual(self.run_sweep(99, 200)[0], 0)
        self.assertEqual(self.run_sweep(99, 200)[0], 0)
        self.assertEqual(self.consumed_ids(), set(range(1, 13)))

if __name__ == '__main__':
    unittest.main()
