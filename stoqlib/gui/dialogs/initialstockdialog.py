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
from sys import maxint as MAXINT

import gtk

from kiwi import ValueUnset
from kiwi.enums import ListType
from kiwi.ui.objectlist import Column
from kiwi.ui.listdialog import ListSlave

from stoqlib.api import api
from stoqlib.domain.product import ProductAdaptToStorable
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _TemporaryStorableItem(object):
    def __init__(self, item):
        self.obj = item
        sellable = item.product.sellable
        self.code = sellable.code
        self.barcode = sellable.barcode
        self.category_description = sellable.get_category_description()
        self.description = sellable.get_description()
        self.initial_stock = 0


class InitialStockDialog(BaseEditor):
    gladefile = "InitialStockDialog"
    model_type = object
    title = _(u"Product  - Initial Stock")
    size = (750, 450)
    help_section = 'stock-register-initial'

    def __init__(self, conn, branch=None):
        if branch is None:
            self._branch = api.get_current_branch(conn)
        else:
            self._branch = branch
        BaseEditor.__init__(self, conn, model=object())
        self._setup_widgets()

    def _setup_widgets(self):
        # XXX: the branch should be in bold font
        self.branch_label.set_text(
            _(u"Registering initial stock for products in %s") %
                                            self._branch.person.name)

        self._storables = [_TemporaryStorableItem(s)
            for s in ProductAdaptToStorable.select(connection=self.conn)
                if s.get_stock_item(self._branch) is None]

        self.slave.listcontainer.add_items(self._storables)

    def _get_columns(self):
        adj = gtk.Adjustment(upper=MAXINT, step_incr=1)
        return [Column("code", title=_(u"Code"), data_type=str,
                       sorted=True, width=100),
                Column("barcode", title=_(u"Barcode"), data_type=str,
                       width=100),
                Column("category_description", title=_(u"Category"),
                       data_type=str, width=100),
                Column("description", title=_(u"Description"),
                       data_type=str, expand=True),
                Column("initial_stock", title=_(u"Initial Stock"),
                       data_type=Decimal, format_func=self._format_qty,
                       editable=True, spin_adjustment=adj, width=115)]

    def _format_qty(self, quantity):
        if quantity is ValueUnset:
            return None
        if quantity >= 0:
            return quantity

    def _validate_initial_stock_quantity(self, item, trans):
        positive = item.initial_stock > 0
        if item.initial_stock is not ValueUnset and positive:
            storable = trans.get(item.obj)
            storable.increase_stock(item.initial_stock, self._branch)

    def _add_initial_stock(self):
        trans = api.new_transaction()
        for item in self._storables:
            self._validate_initial_stock_quantity(item, trans)

        api.finish_transaction(trans, True)
        trans.close()

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
        self._add_initial_stock()
        return True

    def on_cancel(self):
        if self._storables:
            msg = _('Save data before close the dialog ?')
            if yesno(msg, gtk.RESPONSE_NO,
                     _("Save data"),
                     _("Don't save")):
                self._add_initial_stock()
        return False
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
