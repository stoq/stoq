# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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

# pylint: enable=E1101

from decimal import Decimal

from storm.info import get_cls_info
from storm.references import Reference

from stoqlib.database.properties import (UnicodeCol, QuantityCol, DateTimeCol,
                                         PriceCol, IntCol, BoolCol, PercentCol,
                                         IdCol)
from stoqlib.domain.base import Domain
from stoqlib.lib.dateutils import localtoday

# SIGLAS:
# BC - Base de Calculo
# ST - Situação tributária
# CST - Codigo ST
# MVA - Margem de valor adicionado

#
#   Base Tax Classes
#


class BaseTax(Domain):

    def set_item_tax(self, invoice_item, template=None):
        """ Set the tax of an invoice item.

        :param invoice_item: the item of in/out invoice
        """
        template = template or self.get_tax_template(invoice_item)
        if not template:
            return

        for column in get_cls_info(template.__class__).columns:
            if column.name in ['product_tax_template_id', 'te_id', 'id']:
                continue

            value = getattr(template, column.name)
            setattr(self, column.name, value)

        self.set_initial_values(invoice_item)

    @classmethod
    def get_tax_template(cls, invoice_item):  # pragma no cover
        """Use this method in InvoiceItemIpi or InvoiceItemIcms classes to get
        the respective tax template.

        :param invoice_item: the item of in/out invoice
        """
        raise NotImplementedError

    def set_initial_values(self, invoice_item):
        """Use this method to setup the initial values of the fields.
        """
        self.update_values(invoice_item)

    def update_values(self, invoice_item):  # pragma no cover
        pass


class BaseICMS(BaseTax):
    """NfeProductIcms stores the default values that will be used when
    creating NfeItemIcms objects
    """

    # FIXME: this is only used by pylint
    __storm_table__ = 'invalid'

    orig = IntCol(default=None)
    cst = IntCol(default=None)

    mod_bc = IntCol(default=None)
    p_icms = PercentCol(default=None)

    mod_bc_st = IntCol(default=None)
    p_mva_st = PercentCol(default=None)
    p_red_bc_st = PercentCol(default=None)
    p_icms_st = PercentCol(default=None)
    p_red_bc = PercentCol(default=None)

    bc_include_ipi = BoolCol(default=True)
    bc_st_include_ipi = BoolCol(default=True)

    # Simples Nacional
    csosn = IntCol(default=None)
    p_cred_sn = PercentCol(default=None)


class BaseIPI(BaseTax):
    (CALC_ALIQUOTA,
     CALC_UNIDADE) = range(2)

    cl_enq = UnicodeCol(default=u'')
    cnpj_prod = UnicodeCol(default=u'')
    c_selo = UnicodeCol(default=u'')
    q_selo = IntCol(default=None)
    c_enq = UnicodeCol(default=u'')

    cst = IntCol(default=None)
    p_ipi = PercentCol(default=None)

    q_unid = QuantityCol(default=None)

    calculo = IntCol(default=CALC_ALIQUOTA)


#
#   Product Tax Classes
#


class ProductIcmsTemplate(BaseICMS):
    __storm_table__ = 'product_icms_template'

    product_tax_template_id = IdCol()
    product_tax_template = Reference(product_tax_template_id, 'ProductTaxTemplate.id')

    # Simples Nacional
    p_cred_sn_valid_until = DateTimeCol(default=None)

    def is_p_cred_sn_valid(self):
        """Returns if p_cred_sn has expired."""
        if not self.p_cred_sn_valid_until:
            # If we don't have a valid_until, means p_cred_sn will never
            # expire. Therefore, p_cred_sn is valid.
            return True
        elif self.p_cred_sn_valid_until.date() < localtoday().date():
            return False

        return True


class ProductIpiTemplate(BaseIPI):
    __storm_table__ = 'product_ipi_template'
    product_tax_template_id = IdCol()
    product_tax_template = Reference(product_tax_template_id, 'ProductTaxTemplate.id')


class ProductTaxTemplate(Domain):
    (TYPE_ICMS,
     TYPE_IPI) = range(2)

    __storm_table__ = 'product_tax_template'

    types = {TYPE_ICMS: u"ICMS",
             TYPE_IPI: u"IPI"}

    type_map = {TYPE_ICMS: ProductIcmsTemplate,
                TYPE_IPI: ProductIpiTemplate}

    name = UnicodeCol(default=u'')
    tax_type = IntCol()

    def get_tax_model(self):
        klass = self.type_map[self.tax_type]
        store = self.store
        return store.find(klass, product_tax_template=self).one()

    def get_tax_type_str(self):
        return self.types[self.tax_type]


class InvoiceItemIcms(BaseICMS):
    __storm_table__ = 'invoice_item_icms'
    v_bc = PriceCol(default=None)
    v_icms = PriceCol(default=None)

    v_bc_st = PriceCol(default=None)
    v_icms_st = PriceCol(default=None)

    # Simples Nacional
    v_cred_icms_sn = PriceCol(default=None)

    v_bc_st_ret = PriceCol(default=None)
    v_icms_st_ret = PriceCol(default=None)

    def _calc_cred_icms_sn(self, invoice_item):
        if self.p_cred_sn >= 0:
            self.v_cred_icms_sn = invoice_item.get_total() * self.p_cred_sn / 100

    def _calc_st(self, invoice_item):
        self.v_bc_st = invoice_item.price * invoice_item.quantity

        if self.bc_st_include_ipi and invoice_item.ipi_info:
            self.v_bc_st += invoice_item.ipi_info.v_ipi

        if self.p_red_bc_st is not None:
            self.v_bc_st -= self.v_bc_st * self.p_red_bc_st / 100
        if self.p_mva_st is not None:
            self.v_bc_st += self.v_bc_st * self.p_mva_st / 100

        if self.v_bc_st is not None and self.p_icms_st is not None:
            self.v_icms_st = self.v_bc_st * self.p_icms_st / 100
        if self.v_icms is not None and self.v_icms_st is not None:
            self.v_icms_st -= self.v_icms

    def _calc_normal(self, invoice_item):
        self.v_bc = invoice_item.price * invoice_item.quantity

        if self.bc_include_ipi and invoice_item.ipi_info:
            self.v_bc += invoice_item.ipi_info.v_ipi

        if self.p_red_bc is not None:
            self.v_bc -= self.v_bc * self.p_red_bc / 100

        if self.p_icms is not None and self.v_bc is not None:
            self.v_icms = self.v_bc * self.p_icms / 100

    def _update_normal(self, invoice_item):
        """Atualiza os dados de acordo com os calculos do Regime Tributário
        Normal (Não simples)
        """
        if self.cst == 0:
            self.p_red_bc = Decimal(0)
            self._calc_normal(invoice_item)

        elif self.cst == 10:
            self.p_red_bc = Decimal(0)
            self._calc_normal(invoice_item)
            self._calc_st(invoice_item)

        elif self.cst == 20:
            self._calc_normal(invoice_item)

        elif self.cst == 30:
            self.v_icms = 0
            self.v_bc = 0

            self._calc_st(invoice_item)

        elif self.cst in (40, 41, 50):
            self.v_icms = 0
            self.v_bc = 0

        elif self.cst == 51:
            self._calc_normal(invoice_item)

        elif self.cst == 60:
            self.v_bc_st_ret = 0
            self.v_icms_st_ret = 0

        elif self.cst in (70, 90):
            self._calc_normal(invoice_item)
            self._calc_st(invoice_item)

    def _update_simples(self, invoice_item):
        if self.csosn in [300, 400, 500]:
            self.v_bc_st_ret = 0
            self.v_icms_st_ret = 0

        if self.csosn in [101, 201]:
            if self.p_cred_sn is None:
                self.p_cred_sn = Decimal(0)
            self._calc_cred_icms_sn(invoice_item)

        if self.csosn in [201, 202, 203]:
            self._calc_st(invoice_item)

        if self.csosn == 900:
            if self.p_cred_sn is None:
                self.p_cred_sn = Decimal(0)
            self._calc_cred_icms_sn(invoice_item)
            self._calc_normal(invoice_item)
            self._calc_st(invoice_item)

    def update_values(self, invoice_item):
        branch = invoice_item.parent.branch

        # Simples nacional
        if branch.crt in [1, 2]:
            self._update_simples(invoice_item)
        else:
            self._update_normal(invoice_item)

    @classmethod
    def get_tax_template(cls, invoice_item):
        return invoice_item.sellable.product.icms_template


class InvoiceItemIpi(BaseIPI):
    __storm_table__ = 'invoice_item_ipi'
    v_ipi = PriceCol(default=0)
    v_bc = PriceCol(default=None)
    v_unid = PriceCol(default=None)

    def set_initial_values(self, invoice_item):
        self.q_unid = invoice_item.quantity
        self.v_unid = invoice_item.price
        self.update_values(invoice_item)

    def update_values(self, invoice_item):
        # IPI is only calculated if cst is one of the following
        if not self.cst in (0, 49, 50, 99):
            return

        if self.calculo == self.CALC_ALIQUOTA:
            self.v_bc = invoice_item.price * invoice_item.quantity
            if self.p_ipi is not None:
                self.v_ipi = self.v_bc * self.p_ipi / 100
        elif self.calculo == self.CALC_UNIDADE:
            if self.q_unid is not None and self.v_unid is not None:
                self.v_ipi = self.q_unid * self.v_unid

    @classmethod
    def get_tax_template(cls, invoice_item):
        return invoice_item.sellable.product.ipi_template
