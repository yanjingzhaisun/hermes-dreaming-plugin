#!/usr/bin/env python3
"""Run portable regressions and report unavailable optional review suites.

Runtime-dependent suites require the optional test_provider_review.patched_runtime
fixture. Missing optional modules are named skips; other import errors and test
failures are errors. Deployment-only rebuild/sweep suites remain excluded.
"""
from contextlib import nullcontext
import importlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugin/holographic-plus'
sys.path.insert(0, str(PLUGIN))
sys.path.insert(0, str(ROOT / 'tests'))

# Even the store-only suites import Hermes through MemoryStore._init_db().
# Keep the original runtime isolation requirement for all plugin review suites.
OPTIONAL_MODULES = (
    'test_p0', 'test_entities_p0', 'test_timing_phase104',
    'test_semantic_phase106', 'test_provider_review',
    'test_store_review', 'test_review_retrieval',
)
PORTABLE_MODULES = (
    'test_scripts_review', 'test_sweep_recovery',
    'test_sweep_retry_recovery', 'test_sweep_pending_backlog',
)
EXCLUDED_MODULES = {
    'test_rebuild_p0': 'loads deployment-only hp_embedding_rebuild.py outside this repository',
    'test_sweep_p0': 'loads deployment-only sweep/extractor scripts outside this repository',
    'test_run_review': 'subprocess regression; run separately with unittest discovery to avoid recursion',
}


def local_spec(name):
    spec = importlib.util.find_spec(name)
    if spec is not None and (
        spec.origin is None or not Path(spec.origin).resolve().is_relative_to(ROOT)
    ):
        raise RuntimeError(f'Refusing external test module: {name}')
    return spec


def main():
    with tempfile.TemporaryDirectory(prefix='review-suite-', dir=ROOT / 'tests') as home:
        with patch.object(tempfile, 'tempdir', home), patch.dict(
            os.environ, {'HERMES_HOME': home, 'DASHSCOPE_API_KEY': ''}
        ):
            helper = (importlib.import_module('test_provider_review')
                      if local_spec('test_provider_review') is not None else None)
            runtime = helper.patched_runtime(home) if helper is not None else nullcontext()
            with runtime:
                suite = unittest.TestSuite()
                loader = unittest.TestLoader()
                included = 0
                skipped = 0
                for name in OPTIONAL_MODULES + PORTABLE_MODULES:
                    if local_spec(name) is None:
                        if name in PORTABLE_MODULES:
                            raise ModuleNotFoundError(f'Required test module not found: {name}', name=name)
                        print(f'SKIP {name}: optional test module is not bundled in this checkout', flush=True)
                        skipped += 1
                        continue
                    if name in OPTIONAL_MODULES and helper is None:
                        print(f'SKIP {name}: requires missing optional helper '
                              'test_provider_review.patched_runtime for runtime isolation', flush=True)
                        skipped += 1
                        continue
                    module = importlib.import_module(name)
                    if name == 'test_semantic_phase106':
                        module.SCRATCH = home
                    tests = loader.loadTestsFromModule(module)
                    print(f'RUN {name}: {tests.countTestCases()} tests', flush=True)
                    suite.addTests(tests)
                    included += 1
                for name, reason in EXCLUDED_MODULES.items():
                    print(f'SKIP {name}: {reason}', flush=True)
                    skipped += 1
                print(f'Review coverage: {included} suites selected, {skipped} suites skipped', flush=True)
                result = unittest.TextTestRunner(verbosity=2).run(suite)
    return int(not result.wasSuccessful() or result.testsRun == 0)


if __name__ == '__main__':
    raise SystemExit(main())
