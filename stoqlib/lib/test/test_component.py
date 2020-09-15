#
# Copyright (C) 2020 Stoq Tecnologia <http://www.stoq.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
#  Author(s): Stoq Team <stoq-devel@async.com.br>
#

import unittest

from stoqlib.lib.component import (AlreadyImplementedError, Interface, get_utility, provide_utility,
                                   remove_utility, implementer, utilities)

o = object()


class IBanana(Interface):
    pass


class TestUtilities(unittest.TestCase):
    def tearDown(self):
        utilities.clean()

    def testGet(self):
        self.assertEqual(None, get_utility(IBanana, None))
        provide_utility(IBanana, o)
        self.assertRaises(TypeError, get_utility, object)
        self.assertEqual(get_utility(IBanana), o)

    def testProvide(self):
        self.assertRaises(NotImplementedError, get_utility, IBanana)
        provide_utility(IBanana, o)
        self.assertRaises(TypeError, provide_utility, object, o)

    def testRemove(self):
        self.assertRaises(TypeError, remove_utility, object)
        self.assertRaises(NotImplementedError, remove_utility, IBanana)
        provide_utility(IBanana, o)
        self.assertEqual(remove_utility(IBanana), o)
        self.assertRaises(NotImplementedError, remove_utility, IBanana)

    def testAlreadyImplemented(self):
        self.assertRaises(NotImplementedError, get_utility, IBanana)
        provide_utility(IBanana, o)
        self.assertRaises(AlreadyImplementedError,
                          provide_utility, IBanana, o)

    def testZopeInterface(self):
        try:
            from zope.interface import Interface
        except ImportError:
            return

        class IApple(Interface):
            pass

        self.assertRaises(NotImplementedError, get_utility, IApple)
        provide_utility(IApple, o)
        self.assertRaises(AlreadyImplementedError,
                          provide_utility, IApple, o)

    def testImplements(self):
        class I1(Interface):
            pass

        @implementer(I1)
        class C(object):
            pass

        c = C()
        x = object()
        self.assertEqual(I1.providedBy(x), False)
        #self.assertEqual(I1.providedBy(C), False)
        self.assertEqual(I1.providedBy(c), True)

    def testInterfaceSub(self):
        class I1(Interface):
            pass

        class I2(I1):
            pass

        @implementer(I2)
        class C(object):
            pass

        @implementer(I1)
        class D(object):
            pass

        c = C()
        self.assertEqual(I1.providedBy(c), True)
        self.assertEqual(I2.providedBy(c), True)
        d = D()
        self.assertEqual(I1.providedBy(d), True)
        self.assertEqual(I2.providedBy(d), False)

    def testZImplements(self):
        try:
            from zope.interface import Interface, implementer
        except ImportError:
            return

        class I1(Interface):
            pass

        @implementer(I1)
        class C(object):
            pass

        c = C()
        x = object()
        self.assertEqual(I1.providedBy(x), False)
        self.assertEqual(I1.providedBy(C), False)
        self.assertEqual(I1.providedBy(c), True)

    def testZInterfaceSub(self):
        try:
            from zope.interface import Interface, implementer
        except ImportError:
            return

        class I1(Interface):
            pass

        class I2(I1):
            pass

        @implementer(I2)
        class C(object):
            pass

        @implementer(I1)
        class D(object):
            pass

        c = C()
        self.assertEqual(I1.providedBy(c), True)
        self.assertEqual(I2.providedBy(c), True)
        d = D()
        self.assertEqual(I1.providedBy(d), True)
        self.assertEqual(I2.providedBy(d), False)


if __name__ == '__main__':
    unittest.main()
