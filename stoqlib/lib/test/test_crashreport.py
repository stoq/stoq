import unittest

from stoqlib.lib.crashreport import CustomRavenClient


class CrashTestException(AssertionError):
    pass


class CrashTest(unittest.TestCase):
    def initialize(self, exc=Exception):
        text = ('This is a test')
        tb = (exc, exc(text,), None)
        raven_client = CustomRavenClient('https://teste:teste@teste.com.br/4')
        raven_client.ignore = set()
        raven_client.ignore_exceptions = set()
        return text, tb, raven_client

    def test_ignore_exception(self):
        text, tb, raven_client = self.initialize(exc=CrashTestException)
        raven_client.ignore_exceptions.add(CrashTestException)
        self.assertFalse(raven_client.should_capture(tb))

    def test_ignore_exception_by_parent(self):
        text, tb, raven_client = self.initialize(exc=CrashTestException)
        raven_client.ignore_exceptions.add(AssertionError)
        self.assertFalse(raven_client.should_capture(tb))

    def test_ignore_exception_by_name(self):
        text, tb, raven_client = self.initialize(exc=AssertionError)
        raven_client.ignore.add(('AssertionError', text))
        self.assertFalse(raven_client.should_capture(tb))

    def test_dont_ignore_exception(self):
        text, tb, raven_client = self.initialize()
        raven_client.ignore_exceptions.add(CrashTestException)
        raven_client.ignore_exceptions.add(('stoqlib.lib.test.*'))
        self.assertTrue(raven_client.should_capture(tb))
