# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
"""Events.
"""

import datetime

from stoqlib.database.orm import DateTimeCol, IntCol, UnicodeCol
from stoqlib.database.runtime import new_transaction
from stoqlib.domain.base import Domain
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

#
# Domain Classes
#


class Event(Domain):
    """An event represent something that happened in Stoq that
    should be logged and access at a later point.

    @cvar date: the date the event was created
    @cvar description: description of the event
    """

    (TYPE_SYSTEM,
     TYPE_USER,
     TYPE_ORDER,
     TYPE_SALE,
     TYPE_PAYMENT) = range(5)

    types = {# System related messages
             TYPE_SYSTEM: _('System'),
             # Login/Logout
             TYPE_USER: _('User'),
             # Purchase orders
             TYPE_ORDER: _('Order'),
             # Sales
             TYPE_SALE: _('Sale'),
             # Payment
             TYPE_PAYMENT: _('Payment'),
             }

    date = DateTimeCol(default=datetime.datetime.now)
    event_type = IntCol()
    description = UnicodeCol()

    @classmethod
    def log(cls, event_type, description):
        trans = new_transaction()
        cls(event_type=event_type,
            description=description,
            connection=trans)
        trans.commit()
        trans.close()
