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

from stoqdrivers.enum import TaxType

from stoqlib.domain.sellable import Sellable, SellableTaxConstant
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.gui.editors.sellableeditor import SellableTaxConstantEditor
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import info

_ = stoqlib_gettext


class _SellableTaxConstantsListSlave(ModelListSlave):
    model_type = SellableTaxConstant
    editor_class = SellableTaxConstantEditor
    columns = [
        Column('description', _('Description'), data_type=str, expand=True),
        Column('value', _('Tax rate'), data_type=str, width=150),
    ]

    def selection_changed(self, constant):
        if constant is None:
            return
        is_custom = constant.tax_type == TaxType.CUSTOM
        self.listcontainer.remove_button.set_sensitive(is_custom)
        self.listcontainer.edit_button.set_sensitive(is_custom)

    def delete_model(self, model, store):
        sellables = store.find(Sellable, tax_constant=model)
        quantity = sellables.count()
        if quantity > 0:
            msg = _(u"You can't remove this tax, since %d products or "
                    "services are taxed with '%s'.") % (quantity,
                                                        model.get_description())
            info(msg)
        else:
            store.remove(model)

    def run_editor(self, store, model):
        if model and model.tax_type != TaxType.CUSTOM:
            return
        return self.run_dialog(self.editor_class, store=store, model=model)


class SellableTaxConstantsDialog(ModelListDialog):
    list_slave_class = _SellableTaxConstantsListSlave
    size = (500, 300)
    title = _("Taxes")
