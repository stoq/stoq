# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2013 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Payment category, user defined grouping of payments
"""

# pylint: enable=E1101

from zope.interface import implementer

from stoqlib.database.properties import EnumCol, UnicodeCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable


@implementer(IDescribable)
class PaymentCategory(Domain):
    """I am a payment category.
    I contain a name and a color
    """

    __storm_table__ = 'payment_category'

    #: for outgoing payments (payable application)
    TYPE_PAYABLE = u'payable'

    #: for incoming payments (receivable application)
    TYPE_RECEIVABLE = u'receivable'

    #: category name
    name = UnicodeCol()

    #: category color, like #ff0000 for red.
    color = UnicodeCol()

    #: category type, payable or receivable
    category_type = EnumCol(allow_none=False, default=TYPE_PAYABLE)

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.name

    @classmethod
    def get_by_type(cls, store, category_type):
        """Fetches a list of PaymentCategories given a category type

        :param store: a store
        :param category_type: TYPE_PAYABLE or TYPE_RECEIVABLE
        :rseturns: a sequence of PaymentCategory ordered by name
        """
        return store.find(cls, category_type=category_type).order_by(
            PaymentCategory.name)
