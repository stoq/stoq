# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
##
"""Dialog for listing product manufacturers"""

from kiwi.ui.objectlist import Column

from stoqlib.domain.product import ProductManufacturer
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.gui.editors.producteditor import ProductManufacturerEditor
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ProductManufacturerListSlave(ModelListSlave):
    editor_class = ProductManufacturerEditor
    model_type = ProductManufacturer
    columns = [
        Column('name', title=_('Manufacturer'),
               data_type=str, expand=True, sorted=True)
    ]

    def delete_model(self, model, store):
        if not model.can_remove():
            self.refresh()
            warning(_("%s cannot be deleted, because it is used in one or more "
                      "products.") % model.name)
            return
        model = store.fetch(model)
        model.remove()


class ProductManufacturerDialog(ModelListDialog):
    list_slave_class = ProductManufacturerListSlave
    title = _('Manufacturers')
    size = (620, 300)
