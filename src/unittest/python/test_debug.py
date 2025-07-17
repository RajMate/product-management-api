import unittest
import sys

class TestDebug(unittest.TestCase):
    def setUp(self):
        print("Setting up test...", file=sys.stderr)
        sys.stderr.flush()

    def test_debug(self):
        print("Running test_debug...", file=sys.stderr)
        sys.stderr.flush()
        self.assertTrue(True)

    def tearDown(self):
        print("Tearing down test...", file=sys.stderr)
        sys.stderr.flush()

if __name__ == '__main__':
    unittest.main(verbosity=2)