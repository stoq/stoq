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
## Author(s):   Ronaldo Maia            <romaia@async.com.br>
##

from stoqlib.database.orm import (IntCol, UnicodeCol, DecimalCol,
                                  PriceCol, ForeignKey)
from stoqlib.domain.base import Domain, ModelAdapter
from stoqlib.domain.product import Product
from zope.interface import Interface, implements

# SIGLAS:
# BC - Base de Calculo
# ST - Situação tributária
# CST - Codigo ST
# MVA - Margem de valor adicionado


#
#   Base Tax Classes
#

class BaseTax(Domain):

    def set_from_template(self, template):
        if not template:
            return

        for column in template.sqlmeta.columnList:
            value = getattr(template, column.name)
            setattr(self, column.name, value)

class BaseICMS(BaseTax):
    """NfeProductIcms stores the default values that will be used when
    creating NfeItemIcms objects
    """

    orig = IntCol(default=None) # TODOS
    cst = IntCol(default=None) # TODOS

    mod_bc = IntCol(default=None)
    p_icms = DecimalCol(default=None)

    mod_bc_st = IntCol(default=None)
    p_mva_st = DecimalCol(default=None)
    p_red_bc_st = DecimalCol(default=None)
    p_icms_st = DecimalCol(default=None)
    p_red_bc = DecimalCol(default=None)

class BaseIPI(BaseTax):
    cl_enq = UnicodeCol(default='')
    cnpj_prod = UnicodeCol(default='')
    c_selo = UnicodeCol(default='')
    q_selo = IntCol(default=None)
    c_enq = UnicodeCol(default='')

    cst = IntCol(default=None)
    p_ipi = DecimalCol(default=None)

    q_unid = DecimalCol(default=None)


#
#   Product Tax Classes
#


class ProductIcmsTemplate(BaseICMS):
    product_tax_template = ForeignKey('ProductTaxTemplate')


class ProductIpiTemplate(BaseIPI):
    product_tax_template = ForeignKey('ProductTaxTemplate')


class ProductTaxTemplate(Domain):
    (TYPE_ICMS,
     TYPE_IPI) = range(2)

    types = {TYPE_ICMS:     u"ICMS",
             TYPE_IPI:      u"IPI",}

    type_map = {TYPE_ICMS:     ProductIcmsTemplate,
                TYPE_IPI:      ProductIpiTemplate}

    name = UnicodeCol(default='')
    tax_type = IntCol()

    def get_tax_model(self):
        klass = self.type_map[self.tax_type]
        return klass.selectOneBy(product_tax_template=self,
                                 connection=self.get_connection())


    def get_tax_type_str(self):
        return self.types[self.tax_type]




#
#   Sale Item Tax Classes
#

class SaleItemIcms(BaseICMS):
    v_bc = PriceCol(default=None)
    v_icms = PriceCol(default=None)

    v_bc_st = PriceCol(default=None)
    v_icms_st = PriceCol(default=None)


class SaleItemIpi(BaseIPI):
    v_ipi = PriceCol(default=None)
    v_bc = PriceCol(default=None)
    v_unid = PriceCol(default=None)



