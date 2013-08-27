# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

from kiwi.ui.objectlist import Column

from stoqlib.domain.address import Address
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _AddressAdditionListSlave(ModelListSlave):
    model_type = Address
    columns = [
        Column('address_string', title=_('Address'),
               data_type=str, width=250, expand=True),
        Column('city', title=_('City'), width=100,
               data_type=str),
        Column('state', title=_('State'), data_type=str),
    ]

    def populate(self):
        # This is only additional addresses, eg non-main ones
        return self.store.find(Address,
                               person=self.parent.person,
                               is_main_address=False)

    def run_editor(self, store, model):
        from stoqlib.gui.editors.addresseditor import AddressEditor
        store.savepoint('before_run_editor_address')
        retval = self.run_dialog(AddressEditor, store=store,
                                 person=self.parent.person, address=model)
        if not retval:
            store.rollback_to_savepoint('before_run_editor_address')
        return retval


class AddressAdditionDialog(ModelListDialog):
    list_slave_class = _AddressAdditionListSlave
    title = _('Additional Addresses')
    size = (600, 250)

    def __init__(self, store, person, reuse_store=False):
        self.person = person
        self.store = store
        ModelListDialog.__init__(self, store, reuse_store=reuse_store)
