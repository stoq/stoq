# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoqlib/domain/invoice.py'

from stoqlib.domain.invoice import InvoiceLayout, InvoiceField, InvoicePrinter

from stoqlib.domain.test.domaintest import DomainTest


class TestInvoicePrinter(DomainTest):
    def test_get_by_station(self):
        station = self.create_station()
        self.failIf(InvoicePrinter.get_by_station(station, self.store))
        InvoicePrinter(store=self.store,
                       description=u'test invoice',
                       layout=None,
                       device_name=u'/dev/lp0',
                       station=station)
        printer = InvoicePrinter.get_by_station(station, self.store)
        self.failUnless(printer)
        self.assertEqual(printer.station, station)


class TestInvoiceLayout(DomainTest):
    def create_layout(self):
        return InvoiceLayout(description=u'layout',
                             width=10,
                             height=20,
                             store=self.store)

    def test_size(self):
        layout = self.create_layout()
        self.assertEquals(layout.size, (10, 20))

    def test_fields(self):
        layout = self.create_layout()
        self.assertTrue(layout.fields.is_empty())
        field = InvoiceField(layout=layout, x=0, y=0, width=1, height=1,
                             field_name=u'field',
                             store=self.store)
        self.assertFalse(layout.fields.is_empty())
        self.failUnless(field in layout.fields)
        self.assertEquals([field], list(layout.fields))
