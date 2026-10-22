#!/usr/bin/env python3
"""Run local regressions without loading deployment scripts or live services.

The imported rebuild/sweep integration suites need helpers that are deliberately
not bundled. They are excluded here; the portable sweep has its own regressions.
"""
import importlib
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

from test_provider_review import patched_runtime


def main():
    modules = ('test_p0', 'test_entities_p0', 'test_timing_phase104',
               'test_semantic_phase106', 'test_provider_review',
               'test_store_review', 'test_review_retrieval', 'test_scripts_review')
    with tempfile.TemporaryDirectory(prefix='review-suite-', dir=ROOT / 'tests') as home:
        with patch.object(tempfile, 'tempdir', home), patched_runtime(home), patch.dict(
            os.environ, {'HERMES_HOME': home, 'DASHSCOPE_API_KEY': ''}
        ):
            suite = unittest.TestSuite()
            for name in modules:
                module = importlib.import_module(name)
                if not Path(module.__file__).resolve().is_relative_to(ROOT):
                    raise RuntimeError(f'Refusing external test module: {name}')
                if name == 'test_semantic_phase106':
                    module.SCRATCH = home
                suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
            result = unittest.TextTestRunner(verbosity=2).run(suite)
    return int(not result.wasSuccessful())


if __name__ == '__main__':
    raise SystemExit(main())
