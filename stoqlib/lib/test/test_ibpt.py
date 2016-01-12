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

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.taxes import ProductTaxTemplate, ProductIcmsTemplate
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.ibpt import IBPTGenerator, generate_ibpt_message


class TestCalculateTaxForItem(DomainTest):
    def test_with_service(self):
        service = self.create_service()
        sellable = service.sellable
        sale = self.create_sale()
        items = sale.get_items()
        sale.add_sellable(sellable, quantity=1)

        generator = IBPTGenerator(items)
        tax_values = generator._load_tax_values(service)
        federal = generator._calculate_federal_tax(service, tax_values)
        self.assertEquals(federal, Decimal("0"))
        state = generator._calculate_state_tax(service, tax_values)
        self.assertEquals(state, Decimal("0"))

        msg = generate_ibpt_message(sale.get_items())
        expected_msg = ("Trib aprox R$: 0.00 Federal e 0.00 Estadual\n"
                        "Fonte:  0 ")
        self.assertEquals(msg, expected_msg)

    def test_calculate_item_without_ncm(self):
        # Product without NCM
        sale = self.create_sale()
        item = self.create_sale_item(sale)
        items = sale.get_items()
        generator = IBPTGenerator(items)
        tax_values = generator._load_tax_values(item)
        federal = generator._calculate_federal_tax(item, tax_values)
        self.assertEquals(federal, Decimal("0"))
        state = generator._calculate_state_tax(item, tax_values)
        self.assertEquals(state, Decimal("0"))

        msg = generate_ibpt_message(items)
        expected_msg = ("Trib aprox R$: 0.00 Federal e 0.00 Estadual\n"
                        "Fonte:  0 ")
        self.assertEquals(msg, expected_msg)

    def test_calculate_item_without_icms(self):
        # SP (São Paulo) as default state.
        branch = get_current_branch(self.store)
        address = branch.person.get_main_address()
        state = address.city_location.state
        assert state == "SP"
        # Product with NCM, but without ICMS
        sale = self.create_sale()
        item = self.create_sale_item(sale)
        product = item.sellable.product
        product.ncm = u'01012100'
        items = sale.get_items()
        generator = IBPTGenerator(items)
        # When there is no icms information, the value defaults to the nacional
        # tax.
        tax_values = generator._load_tax_values(item)
        federal = generator._calculate_federal_tax(item, tax_values)
        self.assertEquals(federal, Decimal("4.20"))
        state = generator._calculate_state_tax(item, tax_values)
        self.assertEquals(state, Decimal("18"))

        msg = generate_ibpt_message(items)
        expected_msg = ("Trib aprox R$: 4.20 Federal e 18.00 Estadual\n"
                        "Fonte: IBPT ca7gi3 ")
        self.assertEquals(msg, expected_msg)

    def test_calculate_item(self):
        # SP (São Paulo) as default state.
        branch = get_current_branch(self.store)
        address = branch.person.get_main_address()
        state = address.city_location.state
        assert state == "SP"
        # Product with NCM, EX TIPI and ICMS
        sale = self.create_sale()
        sale_item = self.create_sale_item(sale)
        sale_item.price = 150
        product = sale_item.sellable.product
        product.ncm = u'39269090'
        product.ex_tipi = u'001'

        items = sale.get_items()
        generator = IBPTGenerator(items)

        # Create ICMS tax
        tax = ProductTaxTemplate(store=self.store, name=u'Test')
        icms = ProductIcmsTemplate(store=self.store, product_tax_template=tax)
        # Values (0, 3, 4, 5, 8) - taxes codes of brazilian origin.
        # Different values represent taxes of international origin.
        icms.orig = 0
        product.icms_template = icms

        # Values used from IBPT table. Change this values when update the taxes.
        # (ncm;ex;tipo;descricao;nacionalfederal;importadosfederal;estadual;
        #  municipal;vigenciainicio;vigenciafim;chave;versao;fonte;)

        # (39269090;01;0;Ex 01 - Forma para fabricação de calçados;13.45;24.77;18.00;
        #  0.00;01/01/2015;30/06/2015;9oi3aC;15.1.C;IBPT)
        tax_values = generator._load_tax_values(sale_item)
        total_item = sale_item.quantity * sale_item.price
        # Federal tax
        expected_federal_tax = total_item * (Decimal("4.2") / 100)
        federal = generator._calculate_federal_tax(sale_item, tax_values)
        self.assertEquals(federal, expected_federal_tax)
        # State tax
        expected_state_tax = total_item * (Decimal("18") / 100)
        state_tax = generator._calculate_state_tax(sale_item, tax_values)
        self.assertEquals(state_tax, expected_state_tax)

        # With tax of international origin.
        icms.orig = 1
        # Federal tax
        expected_federal_tax = total_item * (Decimal("21.45") / 100)
        federal = generator._calculate_federal_tax(sale_item, tax_values)
        self.assertEquals(federal, expected_federal_tax)
