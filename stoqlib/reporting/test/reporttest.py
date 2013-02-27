# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.diffutils import diff_files
from stoqlib.lib.unittestutils import get_tests_datadir


class ReportTest(DomainTest):
    # FIXME: This should be public
    def _diff_expected(self, report_class, expected_name, *args, **kwargs):
        basedir = get_tests_datadir('reporting')
        expected = os.path.join(basedir, '%s.html' % expected_name)
        output = os.path.join(basedir, '%s-tmp.html' % expected_name)

        def save_report(filename, *args, **kwargs):
            report = report_class(filename, *args, **kwargs)
            report.adjust_for_test()
            report.save_html(filename)

        if not os.path.isfile(expected):
            save_report(expected, *args, **kwargs)
            return

        save_report(output, *args, **kwargs)

        # Diff and compare
        diff = diff_files(expected, output)
        os.unlink(output)

        self.failIf(diff, '%s\n%s' % ("Files differ, output:", diff))
