# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
##
"""
stoq/gui/editors/address.py

    Person address editor implementation.
"""


from kiwi.ui.widgets.list import Column
from stoqlib.gui.lists import AdditionListDialog
from stoqlib.gui.editors import BaseEditor

from stoq.gui.slaves.address import AddressSlave
from stoq.domain.person import Address


class AddressAdditionDialog(AdditionListDialog):
    title = _('Address List')

    def __init__(self, conn, klist_objects, **editor_kwargs):
        cols = self.get_columns()
        AdditionListDialog.__init__(self, conn, self, AddressEditor,
                                    cols, klist_objects, self.title,
                                    **editor_kwargs)
        self.main_address = None

    def get_columns(self):
        return [Column('address_string', title=_('Address'),
                       data_type=str, width=250, expand=True),
                Column('city', title=_('City'), width=100,
                       data_type=str),
                Column('state', title=_('State'), 
                       width=50, data_type=str)]

    def set_main_address(self, main_address):
        if self.main_address:
            self.main_address.is_main_address = False
        self.main_address = main_address



    #
    # AdditionListDialog hooks
    #



    def before_delete_items(self, items):
        assert len(items) >= 1

        for item in items:
            Address.delete(item.id, connection=self.conn)

    def on_add_item(self, model):
        if model.is_main_address:
            self.set_main_address(model)

    def on_edit_item(self, model):
        if model.is_main_address:
            self.set_main_address(model)


class AddressEditor(BaseEditor):
    model_type = Address
    title = _('Address Editor')
    gladefile = 'AddressEditor'

    proxy_widgets = ('is_main_address_checkbutton', )
    widgets = proxy_widgets + ('main_holder', )

    def __init__(self, conn, model=None):
        BaseEditor.__init__(self, conn, model)

    #
    # BaseEditor hooks
    #

    def setup_slaves(self):
        self.address_slave = AddressSlave(self.conn, self.model, False)
        self.proxy.new_model(self.address_slave.model)

        self.attach_slave('main_holder', self.address_slave)

    def setup_proxies(self):
        self.proxy = self.add_proxy(widgets=self.proxy_widgets)

    def on_confirm(self):
        return self.address_slave.on_confirm()


