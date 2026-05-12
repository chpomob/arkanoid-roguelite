#!/usr/bin/env python3
"""Run bot simulation tests (long-running, headless gameplay).

Separate from run_tests.py because these simulate many frames.
Run with: python3 run_simulation_tests.py
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

loader = unittest.TestLoader()
suite = loader.discover('tests', pattern='simulation_slow_test.py')

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

sys.exit(0 if result.wasSuccessful() else 1)
