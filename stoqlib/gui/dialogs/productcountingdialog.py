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
""" Dialog to register the product quantity in stock """

from decimal import Decimal
from sys import maxint as MAXINT

import gtk

from kiwi import ValueUnset
from kiwi.enums import ListType
from kiwi.ui.objectlist import Column
from kiwi.ui.listdialog import ListSlave

from stoqlib.api import api
from stoqlib.domain.inventory import Inventory
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_quantity

_ = stoqlib_gettext


class _TemporaryInventoryItem(object):
    def __init__(self, item):
        self.obj = item
        self.code = item.get_code()
        self.description = item.get_description()
        self.actual_quantity = self.obj.actual_quantity
        self.changed = False


class ProductCountingDialog(BaseEditor):
    gladefile = "HolderTemplate"
    model_type = Inventory
    title = _(u"Product Counting")
    size = (750, 450)

    def __init__(self, model, conn):
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self._inventory_items = self._get_inventory_items()
        self.slave.listcontainer.add_items(self._inventory_items)

    def _get_columns(self):
        #XXX: How to define an upper bound number for our spin button ?
        adj = gtk.Adjustment(upper=MAXINT, step_incr=1)

        return [Column("code", title=_(u"Code"), data_type=str,
                        sorted=True),
                Column("description", title=_(u"Description"),
                        data_type=str, expand=True),
                Column("actual_quantity", title=_(u"Actual quantity"),
                        data_type=Decimal, format_func=self._format_qty,
                        editable=True, spin_adjustment=adj)]

    def _format_qty(self, quantity):
        if quantity is ValueUnset:
            return None
        if quantity >= 0:
            return format_quantity(quantity)

    def _get_inventory_items(self):
        return [_TemporaryInventoryItem(i)
                    for i in self.model.get_items() if not i.adjusted()]

    def _validate_inventory_item(self, item, trans):
        inventory_item = trans.get(item.obj)
        positive = item.actual_quantity >= 0
        if not item.actual_quantity is ValueUnset and positive:
            inventory_item.actual_quantity = item.actual_quantity
        else:
            inventory_item.actual_quantity = None

    def _can_close_inventory_after_counting(self):
        if not self.model.all_items_counted():
            return False

        return not self.model.get_items_for_adjustment()

    def _close_inventory(self):
        # We will close only if the user really wants to.
        # This give the option to the user update the product
        # counting before the adjustment be done.
        msg = _('You have finished the product counting and none '
                'of the products need to be adjusted.\n\n'
                'Would you like to close this inventory now ?')
        if yesno(msg, gtk.RESPONSE_NO, _('Close inventory'),
                                       _('Continue counting')):
            trans = api.new_transaction()
            inventory = trans.get(self.model)
            inventory.close()
            api.finish_transaction(trans, inventory)
            trans.close()

    #
    # BaseEditorSlave
    #

    def setup_slaves(self):
        self.slave = ListSlave(self._get_columns())
        self.slave.set_list_type(ListType.READONLY)
        self.slave.listcontainer.list.connect(
            "cell-edited", self._on_objectlist__cell_edited)
        self.attach_slave("place_holder", self.slave)

    def on_confirm(self):
        trans = api.new_transaction()
        for item in self._inventory_items:
            self._validate_inventory_item(item, trans)

        # We have to call finish_transaction here, since we will check
        # if we can close the inventory now
        api.finish_transaction(trans, True)
        trans.close()

        if self._can_close_inventory_after_counting():
            self._close_inventory()

        return True

    #
    # Callbacks
    #

    def _on_objectlist__cell_edited(self, objectlist, item, attr):
        # After filling a value, jump to the next cell or to the ok
        # button if we are at the last one
        treeview = objectlist.get_treeview()
        rows, column = treeview.get_cursor()
        next_row = rows[0] + 1
        nitems = len(self._inventory_items)
        if next_row < nitems:
            treeview.set_cursor(next_row, column)
        else:
            self.main_dialog.ok_button.grab_focus()
