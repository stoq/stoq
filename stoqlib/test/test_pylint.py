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

from stoqlib.lib.process import Process
from stoqlib.lib.unittestutils import SourceTest
from twisted.trial import unittest


class TestPylint(SourceTest, unittest.TestCase):

    @classmethod
    def filename_filter(cls, filename):
        if (filename.startswith('stoqlib/domain') and
            not filename.startswith('stoqlib/domain/test')):
            return True
        return False

    def check_filename(self, root, filename):
        args = ["pylint",
                "--rcfile=%s/tools/pylint.rcfile" % (self.root,),
                "--load-plugins", "tools/pylint_stoq",
                "-E",
                filename]
        p = Process(args)
        p.wait()
