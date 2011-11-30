import os
import unittest

from stoqlib.lib.interfaces import CookieError
from stoqlib.lib.cookie import Base64CookieFile


class CookieTest(unittest.TestCase):
    def setUp(self):
        self.cookie = Base64CookieFile('test.cookie')

    def _write_cookie(self, data):
        print >> open('test.cookie', "w"), data

    def testGet(self):
        self.assertRaises(CookieError, self.cookie.get)

        self._write_cookie('abc')
        self.assertRaises(CookieError, self.cookie.get)

        self._write_cookie('abc:J')
        self.assertRaises(CookieError, self.cookie.get)

        self._write_cookie('abc:')
        self.assertEqual(self.cookie.get(), ('abc', ''))

        self._write_cookie('abc:YWJj')
        self.assertEqual(self.cookie.get(), ('abc', 'abc'))

        os.remove('test.cookie')

    def testClear(self):
        self.cookie.clear()
        self._write_cookie('abc')
        self.cookie.clear()

        self.failIf(os.path.exists("test.cookie"))

    def testStore(self):
        self._write_cookie('abc')
        os.chmod('test.cookie', 0)
        self.assertRaises(CookieError, self.cookie.store, '', '')
        self.cookie.clear()
        self.cookie.store('abc', 'abc')
        self.assertEqual(open('test.cookie').read(), 'abc:YWJj\n')
        os.remove('test.cookie')
