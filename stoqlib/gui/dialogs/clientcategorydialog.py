# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
"""Dialog for listing client categories"""

from decimal import Decimal

from kiwi.ui.objectlist import Column

from stoqlib.domain.person import ClientCategory
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.gui.editors.clientcategoryeditor import ClientCategoryEditor
from stoqlib.lib.formatters import get_formatted_percentage
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ClientCategoryListSlave(ModelListSlave):
    editor_class = ClientCategoryEditor
    model_type = ClientCategory
    columns = [
        Column('name', title=_('Category'),
               data_type=str, expand=True, sorted=True),
        Column('max_discount', title=_('Max discount'), data_type=Decimal,
               expand=True, format_func=get_formatted_percentage)
    ]

    def delete_model(self, model, store):
        if not model.can_remove():
            self.refresh()
            warning(_("%s cannot be deleted, because is used in one or more "
                      "products.") % model.name)
            return

        model = store.fetch(model)
        model.remove()


class ClientCategoryDialog(ModelListDialog):
    list_slave_class = ClientCategoryListSlave
    title = _('Client categories')
    size = (620, 300)
