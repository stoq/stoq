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

from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.test.domaintest import DomainTest


class TestReturnedSale(DomainTest):
    def testRemove(self):
        sale = self.create_sale()
        self.add_product(sale)
        self.add_product(sale)
        self.add_payments(sale)
        sale.order()
        sale.confirm()
        returned_sale = sale.create_sale_return_adapter()

        total = self.store.find(ReturnedSale, id=returned_sale.id).count()
        total_items = self.store.find(ReturnedSaleItem,
                                      returned_sale_id=returned_sale.id).count()

        self.assertEquals(total, 1)
        self.assertEquals(total_items, 2)

        returned_sale.remove()

        total = self.store.find(ReturnedSale, id=returned_sale.id).count()
        total_items = self.store.find(ReturnedSaleItem,
                                      returned_sale_id=returned_sale.id).count()

        self.assertEquals(total, 0)
        self.assertEquals(total_items, 0)
