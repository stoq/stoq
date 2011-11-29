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
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from stoqlib.domain.taxes import (ProductIcmsTemplate,
                                  ProductTaxTemplate)
from stoqlib.domain.test.domaintest import DomainTest


class TestProductIcmsTemplate(DomainTest):
    """Tests for ProductIcmsTemplate class"""

    def testIsPCredSnValid(self):
        tax_template = ProductTaxTemplate(connection=self.trans,
                                          tax_type=ProductTaxTemplate.TYPE_ICMS)
        icms_template = ProductIcmsTemplate(connection=self.trans,
                                            product_tax_template=tax_template)

        self.assertTrue(icms_template.is_p_cred_sn_valid())

        expire_date = datetime.datetime.today()
        icms_template.p_cred_sn_valid_until = expire_date
        self.assertTrue(icms_template.is_p_cred_sn_valid())

        expire_date = datetime.datetime.today() + relativedelta(days=+1)
        icms_template.p_cred_sn_valid_until = expire_date
        self.assertTrue(icms_template.is_p_cred_sn_valid())

        expire_date = datetime.datetime.today() + relativedelta(days=-1)
        icms_template.p_cred_sn_valid_until = expire_date
        self.assertFalse(icms_template.is_p_cred_sn_valid())


class TestSaleItemIcms(DomainTest):
    """Tests for SaleItemIcms class"""

    def _get_sale_item(self, sale_item_icms=None, quantity=1, price=10):
        sale = self.create_sale()
        product = self.create_product(price=price)
        sale_item = sale.add_sellable(product.sellable, quantity=quantity)

        if sale_item_icms:
            sale_item.icms_info = sale_item_icms

        return sale_item

    def testVCredIcmsSnCalc(self):
        """Test for v_cred_icms_sn calculation.

        This test should fail if v_cred_icms_sn get calculated wrong or gets
        calculated for wrong values of csosn
        """
        # Test for CSOSN 101. This should get v_cred_icms_sn calculated.
        sale_item_icms = self.create_sale_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item_icms.csosn = 101
        sale_item_icms.p_cred_sn = Decimal("3.10")
        expected_v_cred_icms_sn = (sale_item.get_total() *
                                   sale_item_icms.p_cred_sn / 100)
        sale_item_icms.update_values()
        self.assertEqual(sale_item_icms.v_cred_icms_sn,
                         expected_v_cred_icms_sn)

        # Test for CSOSN 201. This should get v_cred_icms_sn calculated.
        sale_item_icms = self.create_sale_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 2, 30)
        sale_item_icms.csosn = 201
        sale_item_icms.p_cred_sn = Decimal("2.90")
        expected_v_cred_icms_sn = (sale_item.get_total() *
                                   sale_item_icms.p_cred_sn / 100)
        sale_item_icms.update_values()
        self.assertEqual(sale_item_icms.v_cred_icms_sn,
                         expected_v_cred_icms_sn)

        # Test for CSOSN 500. This should not get v_cred_icms_sn calculated.
        sale_item_icms = self.create_sale_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item_icms.csosn = 500
        sale_item_icms.p_cred_sn = Decimal("3.10")
        sale_item_icms.update_values()
        self.failIf(sale_item_icms.v_cred_icms_sn)
