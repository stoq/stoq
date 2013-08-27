# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import unittest

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.formatters import (format_phone_number,
                                    format_sellable_description)


class TestFormatters(DomainTest):
    def test_format_sellable_description(self):
        sellable = self.create_sellable()
        sellable.description = u"Cellphone"
        self.assertEqual(format_sellable_description(sellable),
                         u"Cellphone")

        storable = self.create_storable(product=sellable.product)
        batch = self.create_storable_batch(storable=storable,
                                           batch_number=u'666')
        self.assertEqual(format_sellable_description(sellable, batch=batch),
                         u"Cellphone [Batch: 666]")

    def test_format_phone_number(self):
        self.assertEquals(format_phone_number("190"), "190")
        self.assertEquals(format_phone_number("1052"), "1052")
        self.assertEquals(format_phone_number("10325"), "103 25")

        self.assertEquals(format_phone_number("991236789"), "99123-6789")
        self.assertEquals(format_phone_number("0300123456"), "0300 123-456")
        self.assertEquals(format_phone_number("03001234567"), "0300 123-4567")
        self.assertEquals(format_phone_number("0500700600"), "0500 700-600")
        self.assertEquals(format_phone_number("05007006005"), "0500 700-6005")
        self.assertEquals(format_phone_number("0800197878"), "0800 197-878")
        self.assertEquals(format_phone_number("08001234567"), "0800 123-4567")
        self.assertEquals(format_phone_number("0900197878"), "0900 197-878")
        self.assertEquals(format_phone_number("09001234567"), "0900 123-4567")

        self.assertEquals(format_phone_number("1312345678"), "(13) 1234-5678")
        self.assertEquals(format_phone_number("1512345678"), "(15) 1234-5678")
        self.assertEquals(format_phone_number("1812345678"), "(18) 1234-5678")
        self.assertEquals(format_phone_number("1912345678"), "(19) 1234-5678")

        self.assertEquals(format_phone_number("12345678"), "1234-5678")
        self.assertEquals(format_phone_number("1612345678"), "(16) 1234-5678")
        self.assertEquals(format_phone_number("01612345678"), "(16) 1234-5678")
        self.assertEquals(format_phone_number("(16)12345678"), "(16) 1234-5678")
        self.assertEquals(format_phone_number("(016)12345678"), "(16) 1234-5678")
        self.assertEquals(format_phone_number("11123456789"), "(11) 12345-6789")
        self.assertEquals(format_phone_number("011123456789"), "(11) 12345-6789")


if __name__ == '__main__':
    unittest.main()
