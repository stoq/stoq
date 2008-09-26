# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Henrique Romano      <henrique@async.com.br>
##              Lincoln Molica       <lincoln@async.com.br>
##              Johan Dahlin         <jdahlin@async.com.br>
##
""" Slaves for products """

from stoqdrivers.enum import TaxType

from stoqlib.gui.slaves.sellableslave import TributarySituationSlave
from stoqlib.domain.sellable import Sellable, SellableTaxConstant

class ProductTributarySituationSlave(TributarySituationSlave):
    model_type = Sellable

    def setup_combos(self):
        constants = SellableTaxConstant.select(connection=self.trans)
        self.tax_constant.prefill([(c.description, c) for c in constants
                                    if c.tax_type != TaxType.SERVICE])
