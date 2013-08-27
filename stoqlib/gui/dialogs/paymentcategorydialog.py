# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.gui.editors.paymentcategoryeditor import PaymentCategoryEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


def format_category_type(value):
    if value == PaymentCategory.TYPE_PAYABLE:
        return _('Payable')
    elif value == PaymentCategory.TYPE_RECEIVABLE:
        return _('Receivable')


class PaymentCategoryListSlave(ModelListSlave):
    model_type = PaymentCategory
    editor_class = PaymentCategoryEditor
    columns = [
        Column('name', title=_('Category'),
               data_type=str, expand=True, sorted=True),
        Column('category_type', title=_('Type'), data_type=int,
               format_func=format_category_type),
        Column('color', title=_('Color'), width=20,
               data_type=gtk.gdk.Pixbuf, format_func=render_pixbuf),
        Column('color', data_type=unicode, width=120,
               column='color')
    ]

    def populate(self):
        results = super(PaymentCategoryListSlave, self).populate()

        if self.parent.category_type is not None:
            results = results.find(PaymentCategory.category_type == self.parent.category_type)

        return results

    def delete_model(self, model, store):
        for payment in store.find(Payment, category=model):
            payment.category = None
        store.remove(model)

    def run_editor(self, store, model):
        return self.run_dialog(self.editor_class, store=store,
                               model=model,
                               category_type=self.parent.category_type)


class PaymentCategoryDialog(ModelListDialog):
    list_slave_class = PaymentCategoryListSlave
    size = (620, 300)
    title = _('Payment categories')

    def __init__(self, store, category_type=None, reuse_store=False):
        self.category_type = category_type

        ModelListDialog.__init__(self, store, reuse_store=reuse_store)

        column = self.list_slave.listcontainer.list.get_column_by_name('category_type')
        column.treeview_column.set_visible(category_type is None)
