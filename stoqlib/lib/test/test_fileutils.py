# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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

import random
import string
import subprocess
import tempfile
import unittest

from stoqlib.lib.fileutils import md5sum_for_filename


class TestFileUtils(unittest.TestCase):

    def test_md5sum_for_filename(self):
        # Test with a known md5sum
        with tempfile.NamedTemporaryFile() as f:
            f.write('foobar')
            f.flush()

            md5sum = subprocess.check_output(['md5sum', f.name]).split(' ')[0]
            # Make sure the md5sum tool is really working
            self.assertEqual(md5sum, '3858f62230ac3c915f300c664312c63f')
            self.assertEquals(md5sum_for_filename(f.name), md5sum)

        # Test with a random md5sum in a large file
        with tempfile.NamedTemporaryFile() as f:
            for x in xrange(1000000):
                f.write(random.choice(string.printable))
            f.flush()

            md5sum = subprocess.check_output(['md5sum', f.name]).split(' ')[0]
            self.assertEquals(md5sum_for_filename(f.name), md5sum)
