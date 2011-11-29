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

from kiwi.ui.objectlist import Column

from stoqlib.domain.person import ClientCategory, PersonAdaptToClient
from stoqlib.gui.base.lists import ModelListDialog
from stoqlib.gui.editors.clientcategoryeditor import ClientCategoryEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ClientCategoryDialog(ModelListDialog):

    #ModelListDialog
    model_type = ClientCategory
    editor_class = ClientCategoryEditor
    title = _('Client categories')
    size = (620, 300)

    #ListDialog
    columns = [
        Column('name', title=_('Category'),
                data_type=str, expand=True, sorted=True)
        ]

    def delete_model(self, model, trans):
        for client in PersonAdaptToClient.selectBy(category=model,
                                                   connection=trans):
            client.category = None
        ClientCategory.delete(model.id, connection=trans)
