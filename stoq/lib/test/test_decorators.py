import unittest
from stoq.lib.status import threaded


class TestThreaded(unittest.TestCase):
    def test_threaded(self):
        self.call_count = 0

        @threaded
        def task_with_retval():
            self.call_count += 1
            return self.call_count

        value = task_with_retval()
        self.assertEqual(value, 1)

        @threaded
        def task_that_raises():
            self.call_count += 1
            assert False

        with self.assertRaises(AssertionError):
            value = task_that_raises()
