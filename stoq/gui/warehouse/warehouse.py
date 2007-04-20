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
""" Main gui definition for warehouse application.  """

import gettext
import decimal

import gtk
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.widgets.list import Column, SummaryLabel
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.database.database import finish_transaction
from stoqlib.database.runtime import new_transaction, get_current_branch
from stoqlib.domain.interfaces import IBranch, IStorable
from stoqlib.domain.person import Person
from stoqlib.domain.product import ProductAdaptToSellable
from stoqlib.domain.views import ProductFullStockView
from stoqlib.lib.defaults import ALL_BRANCHES
from stoqlib.lib.message import warning
from stoqlib.gui.wizards.receivingwizard import ReceivingOrderWizard
from stoqlib.gui.search.receivingsearch import PurchaseReceivingSearch
from stoqlib.gui.dialogs.productstockdetails import ProductStockHistoryDialog
from stoqlib.gui.dialogs.productretention import ProductRetentionDialog
from stoqlib.reporting.product import ProductReport

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext


class WarehouseApp(SearchableAppWindow):
    app_name = _('Warehouse')
    app_icon_name = 'stoq-warehouse-app'
    gladefile = "warehouse"
    search_table = ProductFullStockView
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
        self.set_text_field_columns(['description', 'supplier_name'])
        self.branch_filter = ComboSearchFilter(
            _('Show products at:'), self._get_branches())
        self.add_filter(self.branch_filter, position=SearchFilterPosition.TOP)
        self.branch_filter.select(get_current_branch(self.conn))
        self.executer.set_query(self.query)

    def get_columns(self):
        return [Column('id', title=_('Code'), sorted=True,
                       data_type=int, format='%03d', width=80),
                Column('description', title=_("Description"),
                       data_type=str, expand=True),
                Column('supplier_name', title=('Supplier'),
                       data_type=str, width=200),
                Column('stock', title=_('Quantity'),
                       data_type=decimal.Decimal, width=90),
                Column('unit', title=_("Unit"), data_type=str,
                       width=70)]

    def query(self, query, conn):
        branch = self.branch_filter.get_state().value
        return self.search_table.select_by_branch(query, branch,
                                                  connection=conn)

    #
    # Private API
    #

    def _setup_widgets(self):
        self.summary_label = SummaryLabel(klist=self.results,
                                          column='stock',
                                          label=_('<b>Stock Total:</b>'),
                                          value_format='<b>%s</b>')
        self.vbox2.pack_start(self.summary_label, False)
        self.vbox2.reorder_child(self.summary_label, 2)
        self.summary_label.show()

    def _get_branches(self):
        items = [(b.person.name, b)
                  for b in Person.iselect(IBranch, connection=self.conn)]
        if not items:
            raise DatabaseInconsistency('You should have at least one '
                                        'branch on your database.'
                                        'Found zero')
        items.insert(0, ALL_BRANCHES)
        return items

    def _update_widgets(self):
        has_stock = len(self.results) > 0
        self.retention_button.set_sensitive(has_stock)
        one_selected = len(self.results.get_selected_rows()) == 1
        self.history_button.set_sensitive(one_selected)
        self.retention_button.set_sensitive(one_selected)
        self.print_button.set_sensitive(has_stock)
        self._update_stock_total()

    def _update_stock_total(self):
        self.summary_label.update_total()

    def _update_filter_slave(self, slave):
        self.refresh()
        self._update_stock_total()

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
        # TODO To be implemented
        pass

    def on_retention_button__clicked(self, button):
        sellable_view = self.results.get_selected_rows()[0]
        storable = IStorable(sellable_view.product, None)
        warehouse_branch = get_current_branch(self.conn)
        if (not storable
            or not storable.get_full_balance(warehouse_branch)):
            warning(_(u"You must have at least one item "
                      "in stock to perfom this action."))
            return
        model = self.run_dialog(ProductRetentionDialog, self.conn,
                                sellable_view.product)
        if not finish_transaction(self.conn, model):
            return
        sellable_view.sync()
        self.results.update(sellable_view)

    def on_receiving_search_action_clicked(self, button):
        self.run_dialog(PurchaseReceivingSearch, self.conn)

    def on_print_button__clicked(self, button):
        results = self.results.get_selected_rows() or self.results
        self.searchbar.print_report(ProductReport, results)

    def on_history_button__clicked(self, button):
        selected = self._klist.get_selected_rows()
        if len(selected) != 1:
            raise ValueError("You should have only one selected item at "
                             "this point")
        sellable = ProductAdaptToSellable.get(selected[0].id,
                                              connection=self.conn)
        self.run_dialog(ProductStockHistoryDialog, self.conn, sellable)
