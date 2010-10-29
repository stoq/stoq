# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## Author(s):   George Y. Kussumoto     <george@async.com.br>
##

from stoqlib.database.orm import (IntCol, UnicodeCol, DecimalCol,
                                  PriceCol)
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

class BaseICMS(Domain):
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

class BaseIPI(Domain):
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
    name = UnicodeCol(default='')


class ProductIpiTemplate(BaseICMS):
    name = UnicodeCol(default='')



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



