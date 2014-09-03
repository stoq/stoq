# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2012 Async Open Source <http://www.async.com.br>
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
"""Logging of events.
"""

# pylint: enable=E1101

# FIXME: This should probably be moved over to stoqlib.domain.logging to
#        avoid confusing it with stoqlib.domain.events.
#        Another possiblity would be to move events out of domain.

from storm.store import AutoReload

from stoqlib.database.properties import DateTimeCol, IntCol, UnicodeCol, EnumCol
from stoqlib.database.orm import ORMObject
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import get_formatted_price, get_formatted_percentage

_ = stoqlib_gettext

#
# Domain Classes
#


class Event(ORMObject):
    """An event represent something that happened in Stoq that
    should be logged and access at a later point.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/event.html>`__

    """

    __storm_table__ = 'event'

    #: System related messages
    TYPE_SYSTEM = u'system'

    #: |loginuser| events, logging in and logging out
    TYPE_USER = u'user'

    #: |purchase| events
    TYPE_ORDER = u'order'

    #: |sale| events
    TYPE_SALE = u'sale'

    #: |payment| events
    TYPE_PAYMENT = u'payment'

    types = {
        TYPE_SYSTEM: _(u'System'),
        TYPE_USER: _(u'User'),
        TYPE_ORDER: _(u'Order'),
        TYPE_SALE: _(u'Sale'),
        TYPE_PAYMENT: _(u'Payment'),
    }

    id = IntCol(primary=True, default=AutoReload)

    #: the date the event was created
    date = DateTimeCol(default_factory=localnow)

    #: type of this event, one of TYPE_* variables of this class
    event_type = EnumCol(allow_none=False, default=TYPE_SYSTEM)

    #: description of the event
    description = UnicodeCol()

    @classmethod
    def log(cls, store, event_type, description):
        """
        Create a new event message.

        :param store: a store
        :param event_type: the event type of this message
        :param description: the message description
        """
        cls(event_type=event_type,
            description=description,
            store=store)

    @classmethod
    def log_sale_item_discount(cls, store, sale_number, user_name, discount_value,
                               product, original_price, new_price):
        """
        Log the discount authorized by an user

        This will log on the event system when a user authorizes a discount
        greater than what is allowed on a sale item

        :param store: a store
        :param sale_number: the sale's id that the discount was applied
        :param user_name: the user that authorized the discount
        :param discount_value: the percentage of discount applied
        :param product: the name of product that received the discount
        :param original_price: the original price of product
        :param new_price: the price of product after discount
        """

        description = _(u"Sale {sale_number}: User {user_name} authorized "
                        u"{discount_value} of discount changing\n "
                        u"{product} value from {original_price} to "
                        u"{new_price}.").format(
            sale_number=sale_number,
            user_name=user_name,
            discount_value=get_formatted_percentage(discount_value),
            product=product,
            original_price=get_formatted_price(original_price, symbol=True),
            new_price=get_formatted_price(new_price, symbol=True))

        cls(event_type=cls.TYPE_SALE,
            description=description,
            store=store)

    @classmethod
    def log_sale_discount(cls, store, sale_number, user_name, discount_value,
                          original_price, new_price):
        """
        Log the discount authorized by an user

        This will log on the event system when a user authorizes a discount
        greater than what is allowed on a sale

        :param store: a store
        :param sale_number: the sale's id that the discount was applied
        :param user_name: the user that authorized the discount
        :param discount_value: the percentage of discount applied
        :param original_price: the original price of product
        :param new_price: the price of product after discount
        """

        description = _(u"sale {sale_number}: User {user_name} authorized "
                        u"{discount_value} of discount changing the value from "
                        u"{original_price} to {new_price}.").format(
            sale_number=sale_number,
            user_name=user_name,
            discount_value=get_formatted_percentage(discount_value),
            original_price=get_formatted_price(original_price, symbol=True),
            new_price=get_formatted_price(new_price, symbol=True))

        cls(event_type=cls.TYPE_SALE,
            description=description,
            store=store)
