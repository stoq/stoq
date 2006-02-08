# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Liaison slave implementation"""

import gettext

from kiwi.ui.widgets.list import Column

from stoqlib.gui.base.lists import AdditionListDialog
from stoqlib.gui.editors.contact import ContactEditor
from stoqlib.lib.validators import format_phone_number
from stoqlib.domain.person import Liaison

_ = gettext.gettext


class LiaisonListDialog(AdditionListDialog):

    def __init__(self, conn, person, liaison_list=None):
        self.person = person
        AdditionListDialog.__init__(self, conn, ContactEditor,
                                    self.get_columns(), liaison_list,
                                    _('Additional Contacts'))
        self.set_before_delete_items(self.before_delete_items)
        self.set_on_add_item(self.on_add_item)

    def get_columns(self):
        return [Column('name', title=_('Name'),
                       data_type=str, expand=True),
                Column('phone_number', title=_('Phone Number'),
                       format_func=format_phone_number,
                       data_type=str, width=200)]

    def get_liaisons(self):
        return self.klist

    #
    # Callbacks
    # 

    def before_delete_items(self, slave, items):
        for item in items:
            Liaison.delete(item.id, connection=self.conn)

    def on_add_item(self, slave, item):
        item.person = self.person
