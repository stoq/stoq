# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
##  Author(s): Evandro Vale Miquelito   <evandro@async.com.br>
##
"""
stoq/gui/slaves/user.py:

    Slaves for users management
"""

import gettext

import gobject
from kiwi.ui.delegates import SlaveDelegate
from kiwi.utils import gsignal

from stoq.domain.person import Person
from stoq.domain.interfaces import IUser
from stoq.lib.defaults import ALL_ITEMS_INDEX

_ = gettext.gettext


class UserStatusSlave(SlaveDelegate):
    gladefile = 'UserStatusSlave'
    
    widgets = ('statuses_combo',)
    gsignal('status-changed')

    def __init__(self):
        SlaveDelegate.__init__(self, gladefile=self.gladefile, 
                               widgets=self.widgets)
        table = Person.getAdapterClass(IUser)
        items = [(value, key) for key, value in table.statuses.items()]
        items.append((_('All Users'), ALL_ITEMS_INDEX))
        self.statuses_combo.prefill(items)
        self.statuses_combo.select_item_by_data(ALL_ITEMS_INDEX)

    def get_selected_status(self):
        return self.statuses_combo.get_selected_data()



    #
    # Kiwi callbacks
    #



    def on_statuses_combo__content_changed(self, *args):
        self.emit('status-changed')

gobject.type_register(UserStatusSlave)
