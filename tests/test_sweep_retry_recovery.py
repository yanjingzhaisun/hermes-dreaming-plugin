"""Offline regressions for nightly retries after the candidate window moves on."""
import unittest
from unittest.mock import patch

from test_sweep_recovery import SweepFixture, state, sweep


class SweepRetryRecovery(SweepFixture):
    def test_failure_before_pending_plan_is_retried_outside_window(self):
        self.add_messages(1, 100)
        with patch.object(sweep, 'atomic_json', side_effect=OSError('injected plan write failure')):
            self.assertEqual(self.run_sweep(0, 200)[0], 1)
        self.assertEqual(len(state.query_failures(self.root / 'shared')), 1)
        self.assertEqual(self.run_sweep(1000, 1200)[0], 0)
        self.assertEqual(self.consumed_ids(), set(range(1, 7)))
        self.assertEqual(state.query_failures(self.root / 'shared'), [])
        code, receipt = self.run_sweep(2000, 2200)
        self.assertEqual(code, 0)
        self.assertEqual(receipt.data['resumed_outside_window'], 0)
        self.assertEqual(receipt.data['skipped_reason'], {'no_candidates': 1})


if __name__ == '__main__':
    unittest.main()
