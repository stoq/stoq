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

import datetime

from stoqlib.domain.taxes import SaleItemIcms
from stoqlib.domain.test.domaintest import DomainTest


class TestSaleItemIcms(DomainTest):
    """Tests for SaleItemIcms class"""

    def _get_sale_item(self, sale_item_icms=None, quantity=1, price=10):
        sale = self.create_sale()
        product = self.create_product(price=price)
        sale_item = sale.add_sellable(product.sellable, quantity=quantity)

        if sale_item_icms:
            sale_item.icms_info = sale_item_icms

        return sale_item

    def testVCredIcmsSn(self):
        # The CSOSN values that should trigger
        # the calculation of v_cred_icms_sn
        csosns_calc_yes = (101, 201) 
        # The CSOSN values that should not trigger
        # the calculation of v_cred_icms_sn
        csosns_calc_not = (500,)
        # Set a value for p_cred_sn for calculations
        p_cred_sn = 3.10

        for csosn in csosns_calc_yes + csosns_calc_not:
            for (quantity, price) in ((1, 10), (2, 10), (2, 20)):
                sale_item_icms = self.create_sale_item_icms()
                sale_item = self._get_sale_item(sale_item_icms,
                                                quantity,
                                                price)
                sale_item_icms.csosn = csosn
                sale_item_icms.p_cred_sn = p_cred_sn
                sale_item_icms.update_values()
                if csosn in csosns_calc_not:
                    # Fail if it made the calc for a csosn that should't do.
                    self.failIf(sale_item_icms.v_cred_icms_sn)
                elif csosn in csosns_calc_yes:
                    expected_v_cred_icms_sn = (sale_item.get_total() *
                                               sale_item_icms.p_cred_sn / 100)
                    self.assertEqual(sale_item_icms.v_cred_icms_sn,
                                     expected_v_cred_icms_sn)


