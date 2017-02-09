# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import unittest
import time

from stoqlib.lib.decorators import cached_property, cached_function, threaded


class TestDecorators(unittest.TestCase):
    def test_cached_property(self):
        class Foo(object):

            def __init__(self):
                self.call_count = 0

            @cached_property(ttl=0)
            def prop(self):
                self.call_count += 1
                return self.call_count

            @cached_property(ttl=1)
            def prop_ttl(self):
                self.call_count += 1
                return self.call_count

        foo = Foo()
        # The first time its called, it should be 1
        self.assertEquals(foo.prop, 1)

        # But the second time, even though we added 1 to the value, it should
        # still return 1
        self.assertEquals(foo.prop, 1)

        # Now testing TTL
        self.assertEquals(foo.prop_ttl, 2)

        # Hopefully, this will get called less than one second after the call
        # above
        self.assertEquals(foo.prop_ttl, 2)

        # Sleep the expected ttl (a bit longer, actually)
        time.sleep(1.1)
        self.assertEquals(foo.prop_ttl, 3)

    def test_cached_function(self):
        self.call_count = 0

        @cached_function()
        def func(arg):
            self.call_count += 1
            return arg

        self.assertEquals(func(1), 1)
        self.assertEquals(self.call_count, 1)

        # Calling it again should not increase call_count
        self.assertEquals(func(1), 1)
        self.assertEquals(self.call_count, 1)

        # but calling with a different argument, should
        self.assertEquals(func('a'), 'a')
        self.assertEquals(self.call_count, 2)

        # Calling a function with a unhashable type should raise a TypeError
        # (this is a programming error really)
        with self.assertRaises(TypeError):
            func({})

    def test_cached_function_keywords(self):
        self.call_count = 0

        @cached_function()
        def func_with_kwargs(foo=1, bar=2):
            self.call_count += 1
            return (foo, bar)

        self.assertEquals(func_with_kwargs(foo=1, bar=2), (1, 2))
        self.assertEquals(self.call_count, 1)

        # Changing the order of the kwargs should not change the call count
        self.assertEquals(func_with_kwargs(bar=2, foo=1), (1, 2))
        self.assertEquals(self.call_count, 1)

        # Calling with positional arguments should also not change call count
        self.assertEquals(func_with_kwargs(1, 2), (1, 2))
        self.assertEquals(self.call_count, 1)

        self.assertEquals(func_with_kwargs(1, bar=2), (1, 2))
        self.assertEquals(self.call_count, 1)

    def test_cached_function_variable(self):
        self.call_count = 0

        # Using different names on purpose (instead of the regular *args,
        # **kwargs)
        @cached_function()
        def func_variable_args(*aaa, **kkk):
            self.call_count += 1
            return (len(aaa), len(kkk))

        self.assertEquals(func_variable_args(1, 2, 3, foo=4, bar=5), (3, 2))
        self.assertEquals(self.call_count, 1)

        self.assertEquals(func_variable_args(1, 2, 3, bar=5, foo=4), (3, 2))
        self.assertEquals(self.call_count, 1)

        self.assertEquals(func_variable_args(1, 2, 4, foo=4, bar=5), (3, 2))
        self.assertEquals(self.call_count, 2)

    def test_cached_function_ttl(self):
        self.call_count = 0

        @cached_function(ttl=1)
        def func(arg):
            self.call_count += 1
            return arg

        self.assertEquals(func(1), 1)
        self.assertEquals(self.call_count, 1)

        # Calling it again should not increase call_count
        self.assertEquals(func(1), 1)
        self.assertEquals(self.call_count, 1)

        # but calling after the ttl, should
        time.sleep(1.1)
        self.assertEquals(func(1), 1)
        self.assertEquals(self.call_count, 2)

    def test_threaded(self):
        self.call_count = 0

        @threaded
        def task_with_retval():
            self.call_count += 1
            return self.call_count

        value = task_with_retval()
        self.assertEquals(value, 1)

        @threaded
        def task_that_raises():
            self.call_count += 1
            assert False

        with self.assertRaises(AssertionError):
            value = task_that_raises()
