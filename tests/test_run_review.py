"""Subprocess regressions for the documented review entry point."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TESTS = Path(__file__).resolve().parent
PORTABLE_MODULES = (
    'test_scripts_review', 'test_sweep_recovery',
    'test_sweep_retry_recovery', 'test_sweep_pending_backlog',
)
PASSING_SUITE = '''import unittest

class Available(unittest.TestCase):
    def test_available(self):
        self.assertTrue(True)
'''


class ReviewRunner(unittest.TestCase):
    def run_review(self, tests):
        return subprocess.run(
            [sys.executable, 'run_review.py'], cwd=tests,
            env={'PATH': os.defpath, 'PYTHONPATH': str(tests),
                 'PYTHONDONTWRITEBYTECODE': '1'},
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=60,
        )

    def run_fixture(self, source):
        with tempfile.TemporaryDirectory(prefix='review-runner-') as directory:
            tests = Path(directory) / 'tests'
            tests.mkdir()
            shutil.copyfile(TESTS / 'run_review.py', tests / 'run_review.py')
            for name in PORTABLE_MODULES:
                (tests / f'{name}.py').write_text(PASSING_SUITE)
            (tests / 'test_scripts_review.py').write_text(source)
            return self.run_review(tests)

    def assert_missing_helper_skips(self, output):
        for name in ('test_provider_review', 'test_store_review', 'test_review_retrieval'):
            self.assertRegex(output, rf'(?m)^SKIP {name}: .*not bundled')
        for name in ('test_p0', 'test_entities_p0', 'test_timing_phase104', 'test_semantic_phase106'):
            self.assertRegex(output, rf'(?m)^SKIP {name}: .*test_provider_review\.patched_runtime')
        for name in PORTABLE_MODULES:
            self.assertIn(f'RUN {name}:', output)

    def test_missing_optional_helper_does_not_abort_available_suites(self):
        result = self.run_review(TESTS)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assert_missing_helper_skips(result.stdout)
        self.assertNotIn('Traceback', result.stdout)
        self.assertIn('\nOK\n', result.stdout)

    def test_available_suite_failure_returns_nonzero(self):
        result = self.run_fixture(PASSING_SUITE.replace(
            'self.assertTrue(True)', "self.fail('injected available-suite failure')"))
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('injected available-suite failure', result.stdout)
        self.assertIn('FAILED (failures=1)', result.stdout)

    def test_unexpected_missing_dependency_is_not_an_optional_skip(self):
        result = self.run_fixture('import missing_required_review_dependency\n')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("No module named 'missing_required_review_dependency'", result.stdout)
        self.assertNotIn('SKIP test_scripts_review:', result.stdout)


if __name__ == '__main__':
    unittest.main()
