# -*- Mode: Python; coding: utf-8 -*-
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

from decimal import Decimal

from stoqlib.domain.taxes import ProductTaxTemplate, ProductIcmsTemplate
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.ibpt import calculate_tax_for_item


class TestCalculateTaxForItem(DomainTest):
    def test_calculate_item_without_ncm(self):
        # Product without NCM
        sale_item = self.create_sale_item()
        tax_value = calculate_tax_for_item(sale_item)
        self.assertEqual(tax_value, Decimal("0"))

    def test_calculate_item_without_icms(self):
        # Product with NCM, but without ICMS
        sale_item = self.create_sale_item()
        product = sale_item.sellable.product
        product.ncm = u'01012100'
        tax_value = calculate_tax_for_item(sale_item)
        # When there is no icms information, the value defaults to the nacional
        # tax.
        self.assertEqual(tax_value, Decimal("26.75"))

    def test_calculate_item(self):
        # Product with NCM, EX TIPI and ICMS
        sale_item = self.create_sale_item()
        sale_item.price = 150
        product = sale_item.sellable.product
        product.ncm = u'39269090'
        product.ex_tipi = u'001'

        # Create ICMS tax
        tax = ProductTaxTemplate(store=self.store, name=u'Test')
        icms = ProductIcmsTemplate(store=self.store, product_tax_template=tax)
        # Values (0, 3, 4, 5, 8) - taxes codes of brazilian origin.
        # Different values represent taxes of international origin.
        icms.orig = 0
        product.icms_template = icms

        # Values used from IBPT table. Change this values when update the taxes.
        # codigo;ex;tabela;descricao;aliqNac;aliqImp;
        # 39269090;01;0;Ex 01 - Forma para fabricação de calçados;20.11;29.27;
        expected_tax = sale_item.price * (Decimal("20.11") / 100)
        tax_value = calculate_tax_for_item(sale_item)
        self.assertEqual(tax_value, Decimal(expected_tax))

        # With tax of international origin.
        icms.orig = 1
        expected_tax = sale_item.price * (Decimal("29.27") / 100)
        tax_value = calculate_tax_for_item(sale_item)
        self.assertEqual(tax_value, Decimal(expected_tax))
