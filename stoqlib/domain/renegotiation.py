# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
##      Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Domain classes for renegotiation management """

from kiwi.datatypes import currency

from stoqlib.database.orm import PriceCol
from stoqlib.database.orm import ForeignKey, UnicodeCol, IntCol
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.base import Domain


_ = stoqlib_gettext


#
# Base Domain Classes
#

class RenegotiationData(Domain):
    """A base class for sale order negotiations

    Note::

        if return_total > 0: the store must return money to customer
        if return_total < 0: the customer must pay to store this value
        if return_total = 0: there is no financial transaction tied with
                             this return operation
    """

    reason = UnicodeCol(default=None)
    paid_total = PriceCol()
    invoice_number = IntCol()
    penalty_value = PriceCol(default=0)
    responsible = ForeignKey('Person')
    sale = ForeignKey('Sale')
    new_order = ForeignKey("Sale", default=None)

    #
    # Accessors
    #

    def get_return_total(self):
        total = self.paid_total - self.penalty_value
        return currency(total)

    def get_new_order_number(self):
        if not self.new_order:
            return u""
        return self.new_order.get_order_number_str()
