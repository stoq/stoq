# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

import mock
from stoqdrivers.printers.virtual.Simple import Simple
from stoqlib.database.runtime import get_current_station
from stoqlib.domain.test.domaintest import DomainTest

from ecf.couponprinter import CouponPrinter
from ecf.ecfdomain import ECFPrinter


class ECFTest(DomainTest):
    def setUp(self):
        super(ECFTest, self).setUp()

        new_store = mock.Mock()
        new_store.return_value = self.store
        get_supported_printers = mock.Mock()
        get_supported_printers.return_value = {u'virtual': [Simple]}
        fake_method = lambda *a, **k: None

        self._mocks = []
        # Fiscal/Coupon printer methods usually creates and
        # commits their transactions.
        self._mocks.append(mock.patch('stoqlib.api.StoqAPI.new_store',
                                      new=new_store))
        self._mocks.append(mock.patch('ecf.couponprinter.new_store',
                                      new=new_store))
        self._mocks.append(mock.patch.object(self.store, 'commit',
                                             new=fake_method))
        self._mocks.append(mock.patch.object(self.store, 'close',
                                             new=fake_method))
        self._mocks.append(mock.patch('stoqdrivers.printers.base.get_supported_printers',
                                      new=get_supported_printers))
        for mocked in self._mocks:
            mocked.start()

        self.ecf_printer = self.create_ecf_printer()
        self.printer = self.create_coupon_printer(self.ecf_printer)

    def tearDown(self):
        for mocked in self._mocks:
            mocked.stop()

        super(ECFTest, self).tearDown()

    def create_ecf_printer(self):
        printer = ECFPrinter(
            store=self.store,
            station=get_current_station(self.store),
            brand=u'virtual',
            model=u'Simple',
            device_name=u'',
            device_serial=u'',
            baudrate=9600,
            is_active=True,
        )
        # This might load state from disk that says that
        # the printer is closed, we don't care about that,
        # so override whatever state was loaded from disk so that
        # the tests can pass.
        printer.till_closed = False
        printer.create_fiscal_printer_constants()
        return printer

    def create_coupon_printer(self, printer=None):
        return CouponPrinter(printer or self.create_ecf_printer())
