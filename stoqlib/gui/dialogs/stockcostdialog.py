# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
""" Dialog to edit the stock average cost for products on a certain branch """

from kiwi import ValueUnset
from kiwi.currency import currency
from kiwi.enums import ListType
from kiwi.ui.objectlist import Column
from kiwi.ui.listdialog import ListSlave

from stoqlib.api import api
from stoqlib.domain.views import ProductWithStockView
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.formatters import get_formatted_cost
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _TemporaryItem(object):
    def __init__(self, item):
        self.obj = item
        self.code = item.code
        self.description = item.description
        self.old_stock_cost = item.stock_cost
        self.stock_cost = item.stock_cost


# FIXME: Create a generic (spreadsheet like) table editor
class StockCostDialog(BaseEditor):
    gladefile = "StockCostDialog"
    model_type = object
    title = _(u"Product - Stock Cost")
    size = (750, 450)

    def __init__(self, store, branch=None):
        if branch is None:
            self._branch = api.get_current_branch(store)
        else:
            self._branch = branch
        BaseEditor.__init__(self, store, model=object())
        self._setup_widgets()

    def _setup_widgets(self):
        self.branch_label.set_markup(
            _(u"Fixing stock cost for products in <b>%s</b>") %
            api.escape(self._branch.get_description()))

        items = ProductWithStockView.find_by_branch(self.store, self._branch)
        self._storables = [_TemporaryItem(s) for s in items]
        self.slave.listcontainer.add_items(self._storables)

    def _get_columns(self):
        return [Column("code", title=_(u"Code"), data_type=str,
                       sorted=True, width=120),
                Column("description", title=_(u"Description"),
                       data_type=str, expand=True),
                Column("stock_cost", title=_(u"Stock Cost"), width=120,
                       data_type=currency, format_func=get_formatted_cost,
                       editable=True)]

    #
    # BaseEditorSlave
    #

    def setup_slaves(self):
        self.slave = ListSlave(self._get_columns())
        self.slave.set_list_type(ListType.READONLY)
        self.slave.listcontainer.list.connect(
            "cell-edited", self._on_objectlist__cell_edited)
        self.attach_slave("on_slave_holder", self.slave)

    def on_confirm(self):
        self.retval = []
        with api.new_store() as store:
            for item in self._storables:
                if (item.stock_cost is ValueUnset or
                        item.stock_cost == item.old_stock_cost or
                        item.stock_cost == 0):
                    continue
                storable = store.fetch(item.obj.product.storable)
                # TODO: add batch information here. Should we edit the the cost of
                # each batch individually, or one cost for all the batches?
                storable.update_stock_cost(item.stock_cost,
                                           self.store.fetch(self._branch))
                self.retval.append(item.obj.product.sellable)

    #
    # Callbacks
    #

    def _on_objectlist__cell_edited(self, objectlist, item, attr):
        # After filling a value, jump to the next cell or to the ok
        # button if we are at the last one
        treeview = objectlist.get_treeview()
        rows, column = treeview.get_cursor()
        next_row = rows[0] + 1
        nitems = len(self._storables)
        if next_row < nitems:
            treeview.set_cursor(next_row, column)
        else:
            objectlist.unselect_all()
            self.main_dialog.ok_button.grab_focus()
