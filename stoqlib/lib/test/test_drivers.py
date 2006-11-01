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
## Author(s):     Henrique Romano <henrique@async.com.br>
##

from stoqlib.lib.drivers import get_fiscal_printer_settings_by_station
from stoqlib.database.runtime import get_current_station

from stoqlib.domain.test.domaintest import DomainTest

class TestDrivers(DomainTest):

    def test_virtual_printer_creation(self):
        station = get_current_station(self.trans)
        settings = get_fiscal_printer_settings_by_station(self.trans,
                                                          station)
        self.failUnless(settings is not None, ("You should have a valid "
                                               "printer at this point."))
        self.failUnless(settings.pm_constants is not None,
                        "You should have the pm_constants defined.")
        self.failUnless(settings.is_custom_pm_configured(),
                        "The pm_constants should be configured.")
