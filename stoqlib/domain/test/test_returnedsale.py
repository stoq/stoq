# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.test.domaintest import DomainTest


class TestReturnedSale(DomainTest):
    @mock.patch.object(ReturnedSale, 'delete')
    @mock.patch.object(ReturnedSaleItem, 'delete')
    def testRemove(self, rsi_delete, rs_delete):
        sale = self.create_sale()
        self.add_product(sale)
        self.add_product(sale)
        returned_sale = sale.create_sale_return_adapter()

        self.assertEqual(rs_delete.call_count, 0)
        self.assertEqual(rsi_delete.call_count, 0)

        returned_sale.remove()

        rs_delete.assert_called_once_with(
            returned_sale.id, store=returned_sale.store)
        # There's no way to use assert_called_with since the mock only stores
        # the last call and we want to make sure the 2 items were removed.
        self.assertEqual(rsi_delete.call_count, 2)
