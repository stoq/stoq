# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Johan Dahlin  <jdahlin@async.com.br>
##

import compiler
import os
import sys
import unittest

import pyflakes

# Mostly Copied from pyflakes script
def check(codeString, filename):
    try:
        tree = compiler.parse(codeString)
    except (SyntaxError, IndentationError):
        value = sys.exc_info()[1]
        (lineno, offset, line) = value[1][1:]
        if line.endswith("\n"):
            line = line[:-1]
        raise AssertionError(
            "could not compile %s:%d: %s" % (filename[9:], lineno, line))
    else:
        w = pyflakes.Checker(tree, filename)
        w.messages.sort(lambda a, b: cmp(a.lineno, b.lineno))
        return list(w.messages)
    return []

def checkPath(filename):
    if os.path.exists(filename):
        return check(file(filename).read(), filename)
    return []

def check_subdirectory(directory):
    warnings = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.py'):
                warnings += checkPath(os.path.join(dirpath, filename))
    return warnings

class PyflakesTest(unittest.TestCase):
    def test_stoqlib(self):
        test_dir = os.path.dirname(__file__)
        stoqlib_dir = os.path.join(test_dir, '..')
        warnings = check_subdirectory(stoqlib_dir)
        if warnings:
            for warning in warnings:
                print str(warning)[9:] # tests/../
            raise AssertionError("%d warnings" % len(warnings))

if __name__ == '__main__':
    unittest.main()
