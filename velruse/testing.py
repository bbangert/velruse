import sys

PY3 = sys.version_info[0] == 3

try:
    import unittest2 as unittest
except ImportError: # pragma: no cover
    if PY3 or sys.version_info[1] >= 7:
        import unittest
    else:
        raise

TestCase = unittest.TestCase
skip = unittest.skip
skipIf = unittest.skipIf
skipUnless = unittest.skipUnless
