# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
""" Domain classes to manage stocks. """

from sqlobject import ForeignKey

from stoqlib.domain.base import InheritableModel
from stoqlib.domain.columns import PriceCol, DecimalCol

#
# Adapters
#

class AbstractStockItem(InheritableModel):
    """A reference to the stock of a certain branch company.

    B{Important attributes}:
        - I{base_cost}: the cost which helps the purchaser to define the
                        main cost of a certain product.
    """

    stock_cost = PriceCol(default=0)
    quantity = DecimalCol(default=0)
    logic_quantity = DecimalCol(default=0)
    branch =  ForeignKey('PersonAdaptToBranch')
