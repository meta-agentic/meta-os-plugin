#!/usr/bin/env python3
"""Run every test of this repository: the one command a contributor and the build both run.

    python3 tests/run.py        every test; exit 1 if any fails
    python3 tests/run.py -q     dots only

Standard library only. Tests are found (`test_*.py` in this folder), not registered.
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(HERE))
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_*.py", top_level_dir=str(HERE))
    result = unittest.TextTestRunner(verbosity=1 if "-q" in argv else 2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
