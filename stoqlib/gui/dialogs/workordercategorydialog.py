# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
"""Dialog for listing payment categories"""

import gtk
from kiwi.ui.gadgets import render_pixbuf
from kiwi.ui.objectlist import Column

from stoqlib.domain.workorder import WorkOrder, WorkOrderCategory
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.gui.editors.workordercategoryeditor import WorkOrderCategoryEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class WorkOrderCategoryListSlave(ModelListSlave):
    model_type = WorkOrderCategory
    editor_class = WorkOrderCategoryEditor
    columns = [
        Column('name', title=_('Category'), data_type=str,
               expand=True, sorted=True),
        Column('color', title=_('Color'), data_type=gtk.gdk.Pixbuf,
               format_func=render_pixbuf),
        Column('color', data_type=str, column='color')
    ]

    def delete_model(self, model, store):
        for workorder in store.find(WorkOrder, category=model):
            workorder.category = None

        super(WorkOrderCategoryListSlave, self).delete_model(model, store)


class WorkOrderCategoryDialog(ModelListDialog):
    list_slave_class = WorkOrderCategoryListSlave
    size = (620, 300)
    title = _('Work order categories')
