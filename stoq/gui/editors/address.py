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
## Author(s):   Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/editors/address.py

    Person address editor implementation.
"""

import gettext

from kiwi.ui.widgets.list import Column
from stoqlib.gui.base.lists import AdditionListDialog
from stoqlib.gui.base.editors import BaseEditor

from stoq.gui.slaves.address import AddressSlave
from stoqlib.domain.person import Address, CityLocation

_ = gettext.gettext


class AddressAdditionDialog(AdditionListDialog):
    title = _('Additional Addresses')

    def __init__(self, conn, klist_objects, **editor_kwargs):
        cols = self.get_columns()
        AdditionListDialog.__init__(self, conn, AddressEditor,
                                    cols, klist_objects, self.title)
        self.register_editor_kwargs(**editor_kwargs)
        self.set_before_delete_items(self.before_delete_items)
        self.set_on_add_item(self.on_add_item)
        self.set_on_edit_item(self.on_edit_item)
        self.main_address = None

    def get_columns(self):
        return [Column('address_string', title=_('Address'),
                       data_type=str, width=250, expand=True),
                Column('city', title=_('City'), width=100,
                       data_type=str),
                Column('state', title=_('State'), data_type=str)]

    def set_main_address(self, main_address):
        if self.main_address:
            self.main_address.is_main_address = False
        self.main_address = main_address

    #
    # Callbacks
    #

    def before_delete_items(self, slave, items):
        assert len(items) >= 1
        for item in items:
            Address.delete(item.id, connection=self.conn)

    def on_add_item(self, slave, model):
        if model.is_main_address:
            self.set_main_address(model)

    def on_edit_item(self, slave, model):
        if model.is_main_address:
            self.set_main_address(model)


class AddressEditor(BaseEditor):
    model_name = _('Address')
    model_type = Address
    gladefile = 'AddressEditor'

    proxy_widgets = ('is_main_address_checkbutton', )

    def __init__(self, conn, model=None, person=None):
        self.person = person
        BaseEditor.__init__(self, conn, model)

    #
    # BaseEditor Hooks
    #

    def create_model(self, conn):
        ct_location = CityLocation(connection=self.conn)
        return Address(connection=self.conn, person=self.person,
                       city_location=ct_location)
        

    def get_title_model_attribute(self, model):
        return self.model_name

    def setup_slaves(self):
        self.address_slave = AddressSlave(self.conn, self.model, False)
        self.proxy.new_model(self.address_slave.model)

        self.attach_slave('main_holder', self.address_slave)

    def setup_proxies(self):
        self.proxy = self.add_proxy(widgets=self.proxy_widgets)

    def on_confirm(self):
        return self.address_slave.on_confirm()
