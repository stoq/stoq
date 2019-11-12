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

from decimal import Decimal

from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from stoqlib import api
from stoqlib.domain.taxes import (ProductCofinsTemplate,
                                  ProductIcmsTemplate,
                                  ProductIpiTemplate,
                                  ProductPisTemplate,
                                  ProductTaxTemplate,
                                  InvoiceItemIpi,
                                  InvoiceItemPis,
                                  InvoiceItemCofins)
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.dateutils import localnow

__tests__ = 'stoqlib/domain/taxes.py'


class TestBaseTax(DomainTest):
    def test_set_item_tax(self):
        icms_template = self.create_product_icms_template()

        tax_template = ProductTaxTemplate(
            store=self.store,
            tax_type=ProductTaxTemplate.TYPE_IPI)
        ipi_template = self.create_product_ipi_template(
            tax_template=tax_template,
            calculo=ProductIpiTemplate.CALC_ALIQUOTA)

        product = self.create_product()
        product.set_icms_template(icms_template)
        product.set_ipi_template(ipi_template)
        sale_item = self.create_sale_item(sellable=product.sellable)
        sale_item.icms_info.set_item_tax(sale_item)
        sale_item.ipi_info.set_item_tax(sale_item)
        sale_item.pis_info.set_item_tax(sale_item)
        sale_item.cofins_info.set_item_tax(sale_item)


class TestProductTaxTemplate(DomainTest):
    def test_get_tax_model(self):
        tax_template = self.create_product_tax_template(tax_type=ProductTaxTemplate.TYPE_ICMS)
        self.assertFalse(tax_template.get_tax_model())
        self.create_product_icms_template(tax_template=tax_template, crt=1)
        self.assertTrue(tax_template.get_tax_model())

    def test_get_tax_type_str(self):
        tax_template = ProductTaxTemplate(
            store=self.store,
            tax_type=ProductTaxTemplate.TYPE_ICMS)
        self.assertEqual(tax_template.get_tax_type_str(), u'ICMS')


class TestProductIcmsTemplate(DomainTest):
    """Tests for ProductIcmsTemplate class"""

    def test_create_simples(self):
        icms_template = self.create_product_icms_template(crt=1)
        self.assertEqual(icms_template.cst, None)
        self.assertNotEqual(icms_template.csosn, None)

    def test_create_normal(self):
        icms_template = self.create_product_icms_template(crt=3)
        self.assertNotEqual(icms_template.cst, None)
        self.assertEqual(icms_template.csosn, None)

    def test_is_p_cred_sn_valid(self):
        icms_template = self.create_product_icms_template(crt=1)

        self.assertTrue(icms_template.is_p_cred_sn_valid())

        expire_date = localnow()
        icms_template.p_cred_sn_valid_until = expire_date
        self.assertTrue(icms_template.is_p_cred_sn_valid())

        expire_date = localnow() + relativedelta(days=+1)
        icms_template.p_cred_sn_valid_until = expire_date
        self.assertTrue(icms_template.is_p_cred_sn_valid())

        expire_date = localnow() + relativedelta(days=-1)
        icms_template.p_cred_sn_valid_until = expire_date
        self.assertFalse(icms_template.is_p_cred_sn_valid())

    def test_mot_des_icms_default(self):
        icms_template = self.create_product_icms_template()

        self.assertIsNone(icms_template.mot_des_icms)

    def test_mot_des_icms_valid(self):
        reasons = (ProductIcmsTemplate.REASON_LIVESTOCK, ProductIcmsTemplate.REASON_OTHERS,
                   ProductIcmsTemplate.REASON_AGRICULTURAL_AGENCY)
        for reason in reasons:
            icms_template = self.create_product_icms_template(mot_des_icms=reason)

            self.assertEqual(icms_template.mot_des_icms, reason)
            self.store.flush()  # should not raise pscycopg2.IntegrityError

    def test_mot_des_icms_invalid(self):
        for mot in (1, 2, 4, 5, 6, 7, 8, 10, 11):
            with api.new_store() as store:
                self.create_product_icms_template(store=store, mot_des_icms=mot)
                with self.assertRaisesRegex(IntegrityError, 'violates check constraint'):
                    store.flush()


class TestInvoiceItemIcms(DomainTest):
    """Tests for InvoiceItemIcms class"""

    def _get_sale_item(self, sale_item_icms=None, quantity=1, price=10):
        sale = self.create_sale()
        product = self.create_product(price=price)
        sale_item = sale.add_sellable(product.sellable, quantity=quantity)
        if sale_item_icms:
            sale_item.icms_info = sale_item_icms

        return sale_item

    def test_calc_v_icms_deson(self):
        sale_item_icms = self.create_invoice_item_icms()
        sale_item_icms.p_icms = 50
        sale_item_icms.v_bc = 2
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)

        sale_item_icms._calc_v_icms_deson(sale_item)

        self.assertEquals(sale_item_icms.v_icms_deson, Decimal('4.00'))

    def test_calc_v_icms_deson_with_zero_value(self):
        sale_item_icms = self.create_invoice_item_icms()
        sale_item_icms.p_icms = 50
        sale_item_icms.v_bc = 2
        sale_item = self._get_sale_item(sale_item_icms, 1, 2)

        sale_item_icms._calc_v_icms_deson(sale_item)

        self.assertEquals(sale_item_icms.v_icms_deson, Decimal('0.01'))

    def testVCredIcmsSnCalc(self):
        """Test for v_cred_icms_sn calculation.

        This test should fail if v_cred_icms_sn get calculated wrong or gets
        calculated for wrong values of csosn
        """
        # Test for CSOSN 101. This should get v_cred_icms_sn calculated.
        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item_icms.csosn = 101
        sale_item_icms.update_values(sale_item)
        sale_item_icms.p_cred_sn = Decimal("3.10")
        expected_v_cred_icms_sn = (sale_item.get_total() *
                                   sale_item_icms.p_cred_sn / 100)
        sale_item_icms.update_values(sale_item)
        self.assertEqual(sale_item_icms.v_cred_icms_sn,
                         expected_v_cred_icms_sn)

        # Test for CSOSN 201. This should get v_cred_icms_sn calculated.
        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 2, 30)
        sale_item_icms.csosn = 201
        sale_item_icms.p_cred_sn = Decimal("2.90")
        expected_v_cred_icms_sn = (sale_item.get_total() *
                                   sale_item_icms.p_cred_sn / 100)
        sale_item_icms.update_values(sale_item)
        self.assertEqual(sale_item_icms.v_cred_icms_sn,
                         expected_v_cred_icms_sn)

        # Test for CSOSN 500. This should not get v_cred_icms_sn calculated.
        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item_icms.csosn = 500
        sale_item_icms.p_cred_sn = Decimal("3.10")
        sale_item_icms.p_fcp_st = 1
        sale_item_icms.p_icms_st = 1
        sale_item_icms.update_values(sale_item)
        self.assertFalse(sale_item_icms.v_cred_icms_sn)
        self.assertEqual(sale_item_icms.p_st, 2)

    def test_update_values_simples(self):
        # Test for CSOSN 900. This should get v_icms and v_icms_st calculated
        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 200)
        sale_item_icms.csosn = 900
        sale_item_icms.p_icms = 1
        sale_item_icms.p_icms_st = 2
        sale_item_icms.p_fcp = 1
        sale_item_icms.p_fcp_st = 2
        sale_item_icms.update_values(sale_item)
        self.assertEqual(sale_item_icms.v_icms, Decimal("2"))
        self.assertEqual(sale_item_icms.v_icms_st, Decimal("2"))
        self.assertEqual(sale_item_icms.v_fcp, Decimal("2"))
        self.assertEqual(sale_item_icms.v_fcp_st, Decimal("2"))

    def test_update_values_normal(self):
        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item.sale.branch.crt = 0
        sale_item_icms.cst = 0
        sale_item_icms.update_values(sale_item)

        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item.sale.branch.crt = 0
        sale_item_icms.cst = 10
        sale_item_icms.p_red_bc_st = 10
        sale_item_icms.p_mva_st = 10
        sale_item_icms.v_bc_st = 10
        sale_item_icms.p_icms_st = 10
        sale_item_icms.p_fcp_st = 2
        sale_item_icms.v_icms = 10
        sale_item_icms.v_fcp = 2
        sale_item_icms.v_icms_st = 10
        sale_item_icms.v_fcp_st = 2
        sale_item_icms.p_red_bc = 10
        sale_item_icms.p_icms = 10
        sale_item_icms.p_fcp = 2
        sale_item_icms.p_v_bc = 10
        sale_item_icms.p_red_bc = 10
        sale_item_icms.update_values(sale_item)

        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item.sale.branch.crt = 0
        sale_item_icms.cst = 20
        sale_item_icms.p_icms = 10
        sale_item_icms.update_values(sale_item)

        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item.sale.branch.crt = 0
        sale_item_icms.cst = 30
        sale_item_icms.p_icms = 10
        sale_item_icms.update_values(sale_item)

        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item.sale.branch.crt = 0
        sale_item_icms.cst = 40
        sale_item_icms.p_icms = 10
        sale_item_icms.update_values(sale_item)

        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item.sale.branch.crt = 0
        sale_item_icms.cst = 51
        sale_item_icms.update_values(sale_item)

        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item.sale.branch.crt = 0
        sale_item_icms.cst = 60
        sale_item_icms.p_fcp_st = 1
        sale_item_icms.p_icms_st = 1
        sale_item_icms.update_values(sale_item)
        self.assertEqual(sale_item_icms.p_st, 2)

        sale_item_icms = self.create_invoice_item_icms()
        sale_item = self._get_sale_item(sale_item_icms, 1, 10)
        sale_item.sale.branch.crt = 0
        sale_item_icms.cst = 70
        sale_item_icms.p_icms = 10
        sale_item_icms.update_values(sale_item)

    def test_v_icms_deson_default(self):
        sale_item_icms = self.create_invoice_item_icms()
        self.assertIsNone(sale_item_icms.v_icms_deson)


class TestProductIpiTemplate(DomainTest):
    def test_create_aliquot(self):
        ipi_template = self.create_product_ipi_template(
            cst=1, cl_enq=u'123', cnpj_prod=u'12.345.678/987-12',
            c_selo=u'123', q_selo=1, c_enq=u'123', p_ipi=2)

        self.assertNotEqual(ipi_template, None)
        self.assertEqual(ipi_template.cst, 1)
        self.assertEqual(ipi_template.calculo, ProductIpiTemplate.CALC_ALIQUOTA)
        self.assertEqual(ipi_template.cl_enq, u'123')
        self.assertEqual(ipi_template.cnpj_prod, u'12.345.678/987-12')
        self.assertEqual(ipi_template.c_selo, u'123')
        self.assertEqual(ipi_template.q_selo, 1)
        self.assertEqual(ipi_template.c_enq, u'123')
        self.assertEqual(ipi_template.p_ipi, 2)

    def test_create_unit(self):
        template = self.create_product_tax_template()
        ipi_template = self.create_product_ipi_template(
            cst=50, c_selo=u'123', q_selo=1, calculo=ProductIpiTemplate.CALC_UNIDADE,
            tax_template=template, cl_enq=u'123', c_enq=u'123', p_ipi=2,
            q_unid=2, cnpj_prod=u'12.345.678/987-12')

        self.assertIsNotNone(ipi_template)
        self.assertEqual(ipi_template.cst, 50)
        self.assertEqual(ipi_template.calculo, ProductIpiTemplate.CALC_UNIDADE)
        self.assertEqual(ipi_template.cl_enq, u'123')
        self.assertEqual(ipi_template.cnpj_prod, u'12.345.678/987-12')
        self.assertEqual(ipi_template.c_selo, u'123')
        self.assertEqual(ipi_template.q_selo, 1)
        self.assertEqual(ipi_template.c_enq, u'123')
        self.assertEqual(ipi_template.p_ipi, 2)
        self.assertEqual(ipi_template.q_unid, 2)


class TestProductPisTemplate(DomainTest):
    def test_create_percentage(self):
        pis_template = self.create_product_pis_template(
            cst=1, p_pis=12)

        self.assertIsNotNone(pis_template)
        self.assertEqual(pis_template.cst, 1)
        self.assertEqual(pis_template.calculo, ProductPisTemplate.CALC_PERCENTAGE)
        self.assertEqual(pis_template.p_pis, 12)

    def test_create_value(self):
        template = self.create_product_tax_template(tax_type='pis')
        pis_template = self.create_product_pis_template(
            cst=50, calculo=ProductPisTemplate.CALC_VALUE,
            p_pis=12, tax_template=template)

        self.assertIsNotNone(pis_template)
        self.assertEqual(pis_template.cst, 50)
        self.assertEqual(pis_template.calculo, ProductPisTemplate.CALC_VALUE)
        self.assertEqual(pis_template.p_pis, 12)

    def test_get_description(self):
        template = self.create_product_tax_template(name='PIS', tax_type='pis')
        pis_template = self.create_product_pis_template(tax_template=template)
        self.assertEqual(pis_template.get_description(), "PIS")


class TestProductCofinsTemplate(DomainTest):
    def test_create_percentage(self):
        calculo = ProductCofinsTemplate.CALC_PERCENTAGE
        cofins_template = self.create_product_cofins_template(
            cst=1, p_cofins=12)

        self.assertIsNotNone(cofins_template)
        self.assertEqual(cofins_template.cst, 1)
        self.assertEqual(cofins_template.calculo, calculo)
        self.assertEqual(cofins_template.p_cofins, 12)

    def test_create_value(self):
        template = self.create_product_tax_template()
        calculo = ProductCofinsTemplate.CALC_VALUE
        cofins_template = self.create_product_cofins_template(
            cst=50, p_cofins=12, tax_template=template, calculo=calculo)

        self.assertIsNotNone(cofins_template)
        self.assertEqual(cofins_template.cst, 50)
        self.assertEqual(cofins_template.calculo, calculo)
        self.assertEqual(cofins_template.p_cofins, 12)

    def test_get_description(self):
        template = self.create_product_tax_template(name='COFINS',
                                                    tax_type='cofins')
        cofins_template = self.create_product_cofins_template(tax_template=template)
        self.assertEqual(cofins_template.get_description(), "COFINS")


class TestInvoiceItemIpi(DomainTest):
    def _get_sale_item(self, sale_item_ipi=None, quantity=1, price=10):
        sale = self.create_sale()
        product = self.create_product(price=price)
        sale_item = sale.add_sellable(product.sellable,
                                      quantity=quantity)
        if sale_item_ipi:
            sale_item.ipi_info = sale_item_ipi

        return sale_item

    def test_set_initial_values(self):
        sale_item_ipi = self.create_invoice_item_ipi()
        sale_item = self._get_sale_item(sale_item_ipi, 1, 10)
        sale_item_ipi.cst = 0
        sale_item_ipi.p_ipi = 0
        sale_item_ipi.set_initial_values(sale_item)

        sale_item_ipi = self.create_invoice_item_ipi()
        sale_item = self._get_sale_item(sale_item_ipi, 1, 10)
        sale_item_ipi.cst = 0
        sale_item_ipi.calculo = InvoiceItemIpi.CALC_UNIDADE
        sale_item_ipi.set_initial_values(sale_item)

        sale_item_ipi = self.create_invoice_item_ipi()
        sale_item = self._get_sale_item(sale_item_ipi, 1, 10)
        sale_item_ipi.cst = 1
        sale_item_ipi.calculo = InvoiceItemIpi.CALC_UNIDADE
        sale_item_ipi.set_initial_values(sale_item)


class TestInvoiceItemPis(DomainTest):

    def _get_sale_item(self, sale_item_pis=None, quantity=1, price=10, cost=None):
        sale = self.create_sale()
        product = self.create_product(price=price)
        sale_item = sale.add_sellable(product.sellable,
                                      quantity=quantity)
        if sale_item_pis:
            sale_item.pis_info = sale_item_pis
        if cost is not None:
            sale_item.average_cost = cost

        return sale_item

    def test_regime_nao_cumulativo(self):
        sale_item_pis = self.create_invoice_item_pis(cst=1, p_pis=Decimal('1.65'))
        sale_item = self._get_sale_item(sale_item_pis, quantity=1, price=10, cost=3)
        sale_item_pis.update_values(sale_item)

        self.assertEqual(sale_item_pis.v_bc, Decimal('7'))  # 10 - 3

    def test_regime_cumulativo(self):
        sale_item_pis = self.create_invoice_item_pis(cst=1, p_pis=Decimal('0.65'))
        sale_item = self._get_sale_item(sale_item_pis, quantity=1, price=10, cost=3)
        sale_item_pis.update_values(sale_item)

        self.assertEqual(sale_item_pis.v_bc, Decimal('10'))  # sale item price

    def test_set_initial_values(self):
        sale_item_pis = self.create_invoice_item_pis(cst=4)
        sale_item = self._get_sale_item(sale_item_pis, 1, 10)
        sale_item_pis.set_initial_values(sale_item)

        self.assertEqual(sale_item_pis.cst, 4)
        self.assertIsNotNone(sale_item_pis.q_bc_prod)
        self.assertIsNone(sale_item_pis.p_pis)
        self.assertIsNone(sale_item_pis.v_bc)
        self.assertEqual(sale_item_pis.v_pis, 0)

        sale_item_pis = self.create_invoice_item_pis(cst=49, p_pis=10,
                                                     calculo=InvoiceItemPis.CALC_PERCENTAGE)
        sale_item = self._get_sale_item(sale_item_pis, 1, 10)
        sale_item_pis.set_initial_values(sale_item)

        self.assertEqual(sale_item_pis.cst, 49)
        self.assertEqual(sale_item_pis.p_pis, 10)
        self.assertEqual(sale_item_pis.v_bc, 10)
        self.assertEqual(sale_item_pis.calculo, InvoiceItemPis.CALC_PERCENTAGE)
        self.assertEqual(sale_item_pis.v_pis, 1)

    def test_pis_simples(self):
        sale_item_pis = self.create_invoice_item_pis(cst=99)
        sale_item = self._get_sale_item(sale_item_pis, 1, 10)
        sale_item_pis.set_initial_values(sale_item)

        self.assertEqual(sale_item_pis.cst, 99)
        self.assertEqual(sale_item_pis.p_pis, 0)
        self.assertEqual(sale_item_pis.v_bc, 0)
        self.assertEqual(sale_item_pis.v_pis, 0)

    def test_get_tax_template(self):
        product = self.create_product()
        service = self.create_service()

        sale_item = self.create_sale_item(sellable=product.sellable)
        sale_item2 = self.create_sale_item(sellable=service.sellable)

        invoice_item_pis = self.create_invoice_item_pis(cst=4)
        pis1 = self.create_product_pis_template()
        pis2 = self.create_product_pis_template()

        with self.sysparam(DEFAULT_PRODUCT_PIS_TEMPLATE=pis1):
            # Product
            self.assertEqual(pis1, invoice_item_pis.get_tax_template(sale_item))
            self.assertNotEqual(pis2, invoice_item_pis.get_tax_template(sale_item))
            # Service
            self.assertEqual(pis1, invoice_item_pis.get_tax_template(sale_item2))
            self.assertNotEqual(pis2, invoice_item_pis.get_tax_template(sale_item2))

        product.set_pis_template(pis2)
        self.assertEqual(pis2, invoice_item_pis.get_tax_template(sale_item))
        self.assertNotEqual(pis1, invoice_item_pis.get_tax_template(sale_item))

        self.assertNotEqual(pis1, invoice_item_pis.get_tax_template(sale_item2))
        self.assertNotEqual(pis2, invoice_item_pis.get_tax_template(sale_item2))


class TestInvoiceItemCofins(DomainTest):

    def _get_sale_item(self, sale_item_cofins=None, quantity=1, price=10, cost=None):
        sale = self.create_sale()
        product = self.create_product(price=price)
        sale_item = sale.add_sellable(product.sellable,
                                      quantity=quantity)
        if sale_item_cofins:
            sale_item.cofins_info = sale_item_cofins

        if cost is not None:
            sale_item.average_cost = cost

        return sale_item

    def test_regime_nao_cumulativo(self):
        sale_item_cofins = self.create_invoice_item_cofins(cst=1, p_cofins=Decimal('7.6'))
        sale_item = self._get_sale_item(sale_item_cofins, quantity=1, price=10, cost=3)
        sale_item_cofins.update_values(sale_item)

        self.assertEqual(sale_item_cofins.v_bc, Decimal('7'))  # 10 - 3

    def test_regime_cumulativo(self):
        sale_item_cofins = self.create_invoice_item_cofins(cst=1, p_cofins=Decimal('3.65'))
        sale_item = self._get_sale_item(sale_item_cofins, quantity=1, price=10, cost=3)
        sale_item_cofins.update_values(sale_item)

        self.assertEqual(sale_item_cofins.v_bc, Decimal('10'))  # sale item price

    def test_set_initial_values(self):
        sale_item_cofins = self.create_invoice_item_cofins(cst=4)
        sale_item = self._get_sale_item(sale_item_cofins, 1, 10)
        sale_item_cofins.set_initial_values(sale_item)

        self.assertEqual(sale_item_cofins.cst, 4)
        self.assertIsNotNone(sale_item_cofins.q_bc_prod)
        self.assertIsNone(sale_item_cofins.p_cofins)
        self.assertIsNone(sale_item_cofins.v_bc)
        self.assertEqual(sale_item_cofins.v_cofins, 0)

        sale_item_cofins = self.create_invoice_item_cofins(
            cst=49, p_cofins=20, calculo=InvoiceItemCofins.CALC_PERCENTAGE)
        sale_item = self._get_sale_item(sale_item_cofins, 1, 10)
        sale_item_cofins.set_initial_values(sale_item)

        self.assertEqual(sale_item_cofins.cst, 49)
        self.assertEqual(sale_item_cofins.p_cofins, 20)
        self.assertEqual(sale_item_cofins.v_bc, 10)
        self.assertEqual(sale_item_cofins.calculo, InvoiceItemCofins.CALC_PERCENTAGE)
        self.assertEqual(sale_item_cofins.v_cofins, 2)

    def test_cofins_simples(self):
        sale_item_cofins = self.create_invoice_item_cofins(cst=99)
        sale_item = self._get_sale_item(sale_item_cofins, 1, 10)
        sale_item_cofins.set_initial_values(sale_item)

        self.assertEqual(sale_item_cofins.cst, 99)
        self.assertEqual(sale_item_cofins.p_cofins, 0)
        self.assertEqual(sale_item_cofins.v_bc, 0)
        self.assertEqual(sale_item_cofins.v_cofins, 0)

    def test_get_tax_template(self):
        product = self.create_product()
        service = self.create_service()

        sale_item = self.create_sale_item(sellable=product.sellable)
        sale_item2 = self.create_sale_item(sellable=service.sellable)

        invoice_item_cofins = self.create_invoice_item_cofins(cst=4)
        cofins1 = self.create_product_cofins_template()
        cofins2 = self.create_product_cofins_template()

        with self.sysparam(DEFAULT_PRODUCT_COFINS_TEMPLATE=cofins1):
            # Product
            self.assertEqual(cofins1, invoice_item_cofins.get_tax_template(sale_item))
            self.assertNotEqual(cofins2, invoice_item_cofins.get_tax_template(sale_item))
            # Service
            self.assertEqual(cofins1, invoice_item_cofins.get_tax_template(sale_item2))
            self.assertNotEqual(cofins2, invoice_item_cofins.get_tax_template(sale_item2))

        product.set_cofins_template(cofins2)
        self.assertEqual(cofins2, invoice_item_cofins.get_tax_template(sale_item))
        self.assertNotEqual(cofins1, invoice_item_cofins.get_tax_template(sale_item))

        self.assertNotEqual(cofins1, invoice_item_cofins.get_tax_template(sale_item2))
        self.assertNotEqual(cofins2, invoice_item_cofins.get_tax_template(sale_item2))
