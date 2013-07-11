# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import os

import unittest

import stoqlib
from stoqlib.lib.process import Process


DISABLED = [
    # Reports
    'similarities',  # Similarity report

    # Convention
    'C0103',  # Invalid name "xxx" for type variable
              #  (should match [a-z_][a-z0-9_]{2,30}$)
    'C0111',  # Missing docstring
    'C0112',  # TODO: Empty docstring
    'C0202',  # Class method xxx should have 'cls' as first argument
    'C0301',  # Line too long
    'C0302',  # Too many lines in module

    # Errors
    'E0211',  # Method has no argument - Interfaces
    'E0213',  # Method should have "self" as first argument - Interfaces
    'E0611',  # Pylint is confused about GTK

    # Fatal
    'F0202',  # Bug in pylint
    #'F0203',  # Bug in pylint (Unable to resolve gtk.XXXX)

    # Info
    'I0011',  # Locally disabling

    # Refactor
    'R0201',  # Method could be a function
    'R0902',  # Too many instance attributes
    'R0903',  # Too few public methods
    'R0904',  # Too many public methods
    'R0911',  # Too many return statements
    'R0912',  # Too many branches
    'R0913',  # Too many arguments
    'R0914',  # Too many local variables

    # Warnings
    'W0101',  # TODO: Unreachable code
    'W0104',  # Statement seems to have no effect
    'W0109',  # TODO: Duplicate key 'XX' in dictionary
    'W0142',  # Used * or ** magic
    'W0201',  # Attribute 'loaded_uis' defined outside __init__
    'W0212',  # Method could be a function (SQLObject from/to_python)
    'W0222',  # Signature differs from overriden method
    'W0221',  # Arguments number differs from overriden method
    'W0223',  # Method 'add' is abstract in class 'xxx' but is not overriden
    'W0232',  # Class has no __init__ method
    'W0404',  # TODO: Reimport 'XX'
    'W0511',  # FIXME/TODO/XXX
    'W0613',  # Unused argument
    'W0621',  # Redefining name 'xxx' from outer scope
    'W0622',  # Redefined built-in variable
    'W0704',  # Except doesn't do anything
]


class TestPylint(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.root = os.path.dirname(
            os.path.dirname(stoqlib.__file__)) + '/'

    def test_stoqlib_domain(self):
        args = ["pylint",
                "--dummy-variables=unused,_",
                "--disable=%s" % (",".join(DISABLED)),
                "--include-ids=y",
                "--load-plugins", "tools/pylint_stoq",
                "--rcfile=%s/tools/pylint.rcfile" % (self.root,),
                "--reports=n",
                "stoqlib.domain"]
        p = Process(args)
        retval = p.wait()
        if retval:
            raise Exception("Pylint errors")
