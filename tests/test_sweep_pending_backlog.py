"""Pending sessions must finish their backlog after rolling-window eligibility expires."""
import json
import unittest
from unittest.mock import patch

from test_sweep_recovery import SweepFixture


class SweepPendingBacklog(SweepFixture):
    def test_default_retry_includes_messages_arriving_after_pending_plan(self):
        self.add_messages(1, 100)
        with patch.object(self.extractor, 'process_sources',
                          side_effect=self.extractor.ProviderExhausted('injected outage')):
            self.assertEqual(self.run_sweep(0, 200)[0], 1)
        self.add_messages(7, 200)
        self.assertEqual(self.run_sweep(1000, 1200)[0], 0)
        self.assertEqual(self.run_sweep(2000, 2200)[0], 0)
        self.assertEqual(self.consumed_ids(), set(range(1, 13)))
        writes = list(self.written)
        self.assertEqual(self.run_sweep(2000, 2200)[0], 0)
        self.assertEqual(self.written, writes)

    def test_default_retry_of_historical_plan_includes_older_backlog(self):
        self.add_messages(1, 10)
        self.add_messages(7, 100)
        with patch.object(self.extractor, 'process_sources',
                          side_effect=self.extractor.ProviderExhausted('injected outage')):
            self.assertEqual(self.run_sweep(99, 200, historical=True)[0], 1)
        self.assertEqual(self.run_sweep(1000, 1200)[0], 0)
        self.assertEqual(self.run_sweep(2000, 2200)[0], 0)
        self.assertEqual(self.consumed_ids(), set(range(1, 13)))

    def test_extended_plan_is_saved_before_writes_and_recovered_after_write_failure(self):
        self.add_messages(1, 100)
        with patch.object(self.extractor, 'process_sources',
                          side_effect=self.extractor.ProviderExhausted('injected outage')):
            self.assertEqual(self.run_sweep(0, 200)[0], 1)
        progress_path = next(self.journal.glob('*.json'))
        original = progress_path.read_bytes()
        original_pending = json.loads(original)['pending']
        self.add_messages(7, 200)
        with patch('fact_extract_sweep.atomic_json',
                   side_effect=OSError('injected extended plan write failure')):
            self.assertEqual(self.run_sweep(1000, 1200)[0], 1)
        self.assertEqual(progress_path.read_bytes(), original)
        self.assertEqual(self.written, [])

        process = self.extractor.process_sources

        def assert_saved_plan(sid, chunks, *args, **kwargs):
            saved = json.loads(progress_path.read_text())
            self.assertEqual(saved['pending'], chunks)
            self.assertEqual(chunks[:len(original_pending)], original_pending)
            return process(sid, chunks, *args, **kwargs)

        with patch.object(self.extractor, 'process_sources', side_effect=assert_saved_plan):
            self.assertEqual(self.run_sweep(2000, 2200)[0], 0)
        self.assertEqual(self.consumed_ids(), set(range(1, 13)))


if __name__ == '__main__':
    unittest.main()
