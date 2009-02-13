# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Main gui definition for stock application.  """

import gettext
import decimal

import pango
import gtk
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.objectlist import Column, SearchColumn
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.database.runtime import (new_transaction, get_current_branch,
                                      finish_transaction)
from stoqlib.domain.interfaces import IBranch, IStorable
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.person import Person
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import ProductWithStockView
from stoqlib.lib.message import warning
from stoqlib.gui.wizards.receivingwizard import ReceivingOrderWizard
from stoqlib.gui.wizards.stocktransferwizard import StockTransferWizard
from stoqlib.gui.search.receivingsearch import PurchaseReceivingSearch
from stoqlib.gui.search.productsearch import ProductSearchQuantity
from stoqlib.gui.search.purchasesearch import PurchasedItemsSearch
from stoqlib.gui.search.transfersearch import TransferOrderSearch
from stoqlib.gui.dialogs.initialstockdialog import InitialStockDialog
from stoqlib.gui.dialogs.openinventorydialog import show_inventory_process_message
from stoqlib.gui.dialogs.productstockdetails import ProductStockHistoryDialog
from stoqlib.gui.dialogs.productretention import ProductRetentionDialog
from stoqlib.reporting.product import ProductReport

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext


class StockApp(SearchableAppWindow):
    app_name = _('Stock')
    app_icon_name = 'stoq-stock-app'
    gladefile = "stock"
    search_table = ProductWithStockView
    search_labels = _('Matching:')
    klist_selection_mode = gtk.SELECTION_MULTIPLE

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._setup_widgets()
        self._update_widgets()

    #
    # SearchableAppWindow
    #

    def create_filters(self):
        self.executer.set_query(self.query)
        self.set_text_field_columns(['description'])
        self.branch_filter = ComboSearchFilter(
            _('Show products at:'), self._get_branches())
        self.branch_filter.select(get_current_branch(self.conn))
        self.add_filter(self.branch_filter, position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [SearchColumn('id', title=_('Code'), sorted=True,
                             data_type=int, format='%03d', width=80),
                SearchColumn('barcode', title=_("Barcode"), data_type=str,
                             width=100),
                SearchColumn('description', title=_("Description"),
                             data_type=str, expand=True,
                             ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('stock', title=_('Quantity'),
                             data_type=decimal.Decimal, width=100),
                SearchColumn('unit', title=_("Unit"), data_type=str,
                             width=80)]

    def query(self, query, having, conn):
        branch = self.branch_filter.get_state().value
        return self.search_table.select_by_branch(query, branch,
                                                  having=having,
                                                  connection=conn)

    #
    # Private API
    #

    def _setup_widgets(self):
        self.search.set_summary_label(column='stock',
                                      label=_('<b>Stock Total:</b>'),
                                      format='<b>%s</b>')

        if Inventory.has_open(self.conn, get_current_branch(self.conn)):
            show_inventory_process_message()

    def _get_branches(self):
        items = [(b.person.name, b)
                  for b in Person.iselect(IBranch, connection=self.conn)]
        if not items:
            raise DatabaseInconsistency('You should have at least one '
                                        'branch on your database.'
                                        'Found zero')
        items.insert(0, [_('All branches'), None])
        return items

    def _update_widgets(self):
        branch = get_current_branch(self.conn)
        if Inventory.has_open(self.conn, branch):
            self.retention_button.set_sensitive(False)
            self.transfer_action.set_sensitive(False)
            self.receive_action.set_sensitive(False)
            self.initial_stock_action.set_sensitive(False)
            return

        is_main_branch = self.branch_filter.get_state().value is branch
        has_stock = len(self.results) > 0
        one_selected = len(self.results.get_selected_rows()) == 1
        self.history_button.set_sensitive(one_selected and is_main_branch)
        self.retention_button.set_sensitive(one_selected and is_main_branch)
        self.print_button.set_sensitive(has_stock)
        # We need more than one branch to be able to do transfers
        # Note that 'all branches' is not a real branch
        has_branches = len(self.branch_filter.combo) > 2

        self.transfer_action.set_sensitive(has_branches)
        self.TransferSearch.set_sensitive(has_branches)

    def _update_filter_slave(self, slave):
        self.refresh()

    def _retend_stock(self, sellable_view):
        storable = IStorable(sellable_view.product, None)
        warehouse_branch = get_current_branch(self.conn)
        if (not storable
            or not storable.get_full_balance(warehouse_branch)):
            warning(_(u"You must have at least one item "
                      "in stock to perfom this action."))
            return
        trans = new_transaction()
        product = trans.get(sellable_view.product)
        model = self.run_dialog(ProductRetentionDialog, trans,
                                product)
        if not finish_transaction(trans, model):
            return
        self.refresh()

    def _transfer_stock(self):
        trans = new_transaction()
        model = self.run_dialog(StockTransferWizard, trans)
        finish_transaction(trans, model)
        trans.close()

    #
    # Callbacks
    #

    def on_results__selection_changed(self, results, product):
        self._update_widgets()

    def _on_receive_action_clicked(self, button):
        trans = new_transaction()
        model = self.run_dialog(ReceivingOrderWizard, trans)
        finish_transaction(trans, model)
        trans.close()

    def on_stock_transfer_action_clicked(self, button):
        self._transfer_stock()

    def on_transfer_action__activate(self, action):
        self._transfer_stock()

    def on_TransferSearch__activate(self, action):
        self.run_dialog(TransferOrderSearch, self.conn)

    def on_PurchasedItemsSearch__activate(self, action):
        self.run_dialog(PurchasedItemsSearch, self.conn)

    def on_retention_button__clicked(self, button):
        sellable_view = self.results.get_selected_rows()[0]
        self._retend_stock(sellable_view)

    def on_ProductHistory__activate(self, action):
        self.run_dialog(ProductSearchQuantity, self.conn)

    def on_initial_stock_action__activate(self, action):
        branch = self.branch_filter.get_state().value
        self.run_dialog(InitialStockDialog, self.conn, branch)

    def on_receiving_search_action_clicked(self, button):
        self.run_dialog(PurchaseReceivingSearch, self.conn)

    def on_print_button__clicked(self, button):
        results = self.results.get_selected_rows() or self.results
        branch_name = self.branch_filter.combo.get_active_text()
        self.print_report(ProductReport, results, branch_name=branch_name)

    def on_history_button__clicked(self, button):
        selected = self._klist.get_selected_rows()
        if len(selected) != 1:
            raise ValueError("You should have only one selected item at "
                             "this point")
        sellable = Sellable.get(selected[0].id, connection=self.conn)
        self.run_dialog(ProductStockHistoryDialog, self.conn, sellable,
                        branch=self.branch_filter.combo.get_selected())
