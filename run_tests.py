#!/usr/bin/env python3
"""Run fast unit tests (excludes slow simulation tests).

Use run_simulation_tests.py for long-running bot simulation tests.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

loader = unittest.TestLoader()
suite = loader.discover('tests')

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

sys.exit(0 if result.wasSuccessful() else 1)
