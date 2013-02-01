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

# FIXME: This should probably be moved over to stoqlib.domain.logging to
#        avoid confusing it with stoqlib.domain.events.
#        Another possiblity would be to move events out of domain.
import datetime

from storm.store import AutoReload

from stoqlib.database.properties import DateTimeCol, IntCol, UnicodeCol
from stoqlib.database.orm import ORMObject
from stoqlib.database.runtime import new_store
from stoqlib.lib.translation import stoqlib_gettext

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
    TYPE_SYSTEM = 0

    #: |loginuser| events, logging in and logging out
    TYPE_USER = 1

    #: |purchase| events
    TYPE_ORDER = 2

    #: |sale| events
    TYPE_SALE = 3

    #: |payment| events
    TYPE_PAYMENT = 4

    types = {
             TYPE_SYSTEM: _(u'System'),
             TYPE_USER: _(u'User'),
             TYPE_ORDER: _(u'Order'),
             TYPE_SALE: _(u'Sale'),
             TYPE_PAYMENT: _(u'Payment'),
             }

    id = IntCol(primary=True, default=AutoReload)

    #: the date the event was created
    date = DateTimeCol(default_factory=datetime.datetime.now)

    #: type of this event, one of TYPE_* variables of this class
    event_type = IntCol()

    #: description of the event
    description = UnicodeCol()

    @classmethod
    def log(cls, event_type, description):
        """
        Create a new event message.

        :param event_type: the event type of this message
        :param description: the message description

        .. note:: this creates a new store, commits and closes it.
        """
        store = new_store()
        cls(event_type=event_type,
            description=description,
            store=store)
        store.commit()
        store.close()
