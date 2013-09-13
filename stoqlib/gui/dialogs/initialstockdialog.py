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
""" Dialog to register the initial stock of a product in a certain branch """

from decimal import Decimal

import gtk
from kiwi import ValueUnset
from kiwi.currency import currency
from kiwi.enums import ListType
from kiwi.python import Settable
from kiwi.ui.objectlist import Column
from kiwi.ui.listdialog import ListSlave

from stoqlib.api import api
from stoqlib.domain.person import Branch
from stoqlib.domain.product import Storable
from stoqlib.domain.sellable import SellableCategory
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.batchselectiondialog import BatchIncreaseSelectionDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.defaults import MAX_INT
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _TemporaryStorableItem(object):
    def __init__(self, sellable, product, storable):
        self.storable = storable

        self.code = sellable.code
        self.barcode = sellable.barcode
        self.category_description = sellable.get_category_description()
        self.description = sellable.get_description()
        self.unit_cost = sellable.cost
        self.is_batch = self.storable and self.storable.is_batch
        self.batches = {}
        if not self.is_batch:
            self.initial_stock = 0

    @property
    def initial_stock(self):
        if self.is_batch:
            return sum(quantity for quantity in self.batches.values())
        return self._quantity

    @initial_stock.setter
    def initial_stock(self, quantity):
        assert not self.is_batch
        self._quantity = quantity


class InitialStockDialog(BaseEditor):
    gladefile = "InitialStockDialog"
    model_type = Settable
    title = _(u"Initial Stock")
    size = (850, 450)
    help_section = 'stock-register-initial'
    proxy_widgets = ['branch']

    need_cancel_confirmation = True

    #
    # Private
    #

    def _refresh_storables(self):
        self.slave.listcontainer.list.add_list(self._get_storables())

    def _get_storables(self):
        self._current_branch = self.model.branch
        # Cache this data, to avoid more queries when building the list of storables.
        self._categories = list(self.store.find(SellableCategory))
        data = Storable.get_initial_stock_data(self.store, self.model.branch)
        for sellable, product, storable in data:
            yield _TemporaryStorableItem(sellable, product, storable)

    def _get_columns(self):
        adj = gtk.Adjustment(lower=0, upper=MAX_INT, step_incr=1)
        return [Column("code", title=_(u"Code"), data_type=str, sorted=True,
                       width=100),
                Column("barcode", title=_(u"Barcode"), data_type=str,
                       width=100),
                Column("category_description", title=_(u"Category"),
                       data_type=str, width=100),
                Column("description", title=_(u"Description"),
                       data_type=str, expand=True),
                Column('manufacturer', title=_("Manufacturer"),
                       data_type=str, visible=False),
                Column('model', title=_("Model"),
                       data_type=str, visible=False),
                Column("initial_stock", title=_(u"Initial Stock"),
                       data_type=Decimal, format_func=self._format_qty,
                       editable=True, spin_adjustment=adj, width=110),
                Column("unit_cost", title=_(u"Unit Cost"), width=90,
                       data_type=currency, editable=True, spin_adjustment=adj)]

    def _format_qty(self, quantity):
        if quantity is ValueUnset:
            return None
        if quantity >= 0:
            return quantity

    def _validate_initial_stock_quantity(self, item):
        if ValueUnset in [item.initial_stock, item.unit_cost]:
            return

        valid_stock = item.initial_stock > 0
        valid_cost = item.unit_cost >= 0
        if valid_stock and valid_cost:
            storable = item.storable
            if item.is_batch:
                for batch, quantity in item.batches.items():
                    storable.register_initial_stock(quantity,
                                                    self.model.branch,
                                                    item.unit_cost,
                                                    batch_number=batch)
            else:
                storable.register_initial_stock(item.initial_stock,
                                                self.model.branch,
                                                item.unit_cost)

    def _add_initial_stock(self):
        for item in self.storables:
            self._validate_initial_stock_quantity(item)

    #
    # BaseEditorSlave
    #

    def create_model(self, store):
        self._current_branch = api.get_current_branch(store)
        return Settable(branch=self._current_branch)

    def setup_proxies(self):
        if api.sysparam.get_bool('SYNCHRONIZED_MODE'):
            current = api.get_current_branch(self.store)
            branches = [(current.get_description(), current)]
        else:
            branches = api.for_combo(Branch.get_active_branches(self.store))

        self.branch.prefill(branches)
        self.add_proxy(self.model, self.proxy_widgets)

    def setup_slaves(self):
        self.slave = ListSlave(self._get_columns())
        self.slave.set_list_type(ListType.READONLY)
        self.storables = self.slave.listcontainer.list
        self.storables.set_cell_data_func(
            self._on_storables__cell_data_func)
        self.attach_slave("on_slave_holder", self.slave)

        self._refresh_storables()

    def on_confirm(self):
        self._add_initial_stock()

    def has_changes(self):
        return any(i.initial_stock > 0 for i in self.storables)

    #
    # Callbacks
    #

    def _on_storables__cell_data_func(self, column, renderer, obj, text):
        if not isinstance(renderer, gtk.CellRendererText):
            return text

        if column.attribute == 'initial_stock':
            renderer.set_property('editable-set', not obj.is_batch)
            renderer.set_property('editable', not obj.is_batch)

        return text

    def on_storables__row_activated(self, storables, item):
        if item.is_batch:
            retval = run_dialog(BatchIncreaseSelectionDialog, self,
                                store=self.store, model=item.storable,
                                quantity=0, original_batches=item.batches)
            item.batches = retval or item.batches
            self.storables.update(item)

    def on_storables__cell_edited(self, storables, item, attr):
        # After filling a value, jump to the next cell or to the ok
        # button if we are at the last one
        treeview = storables.get_treeview()
        rows, column = treeview.get_cursor()
        next_row = rows[0] + 1
        nitems = len(self.storables)
        if next_row < nitems:
            treeview.set_cursor(next_row, column)
        else:
            storables.unselect_all()
            self.main_dialog.ok_button.grab_focus()

    def after_branch__content_changed(self, widget):
        # There is a little bug in kiwi that causes this signal to be emmited
        # after just losing focus
        if self.model.branch == self._current_branch:
            return
        self._refresh_storables()
