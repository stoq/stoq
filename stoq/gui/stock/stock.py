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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Main gui definition for stock application.  """

import gettext
import decimal

import pango
import gtk
from kiwi.datatypes import converter
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.objectlist import Column, SearchColumn
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.database.runtime import (new_transaction, get_current_branch,
                                      finish_transaction)
from stoqlib.domain.interfaces import IBranch
from stoqlib.domain.person import Person
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import ProductFullStockView
from stoqlib.lib.defaults import sort_sellable_code
from stoqlib.gui.editors.producteditor import ProductStockEditor
from stoqlib.gui.help import show_contents, show_section
from stoqlib.gui.wizards.loanwizard import NewLoanWizard, CloseLoanWizard
from stoqlib.gui.wizards.receivingwizard import ReceivingOrderWizard
from stoqlib.gui.wizards.stocktransferwizard import StockTransferWizard
from stoqlib.gui.wizards.stockdecreasewizard import StockDecreaseWizard
from stoqlib.gui.search.loansearch import LoanItemSearch, LoanSearch
from stoqlib.gui.search.receivingsearch import PurchaseReceivingSearch
from stoqlib.gui.search.productsearch import (ProductSearchQuantity,
                                              ProductStockSearch,
                                              ProductClosedStockSearch)
from stoqlib.gui.search.purchasesearch import PurchasedItemsSearch
from stoqlib.gui.search.transfersearch import TransferOrderSearch
from stoqlib.gui.search.stockdecreasesearch import StockDecreaseSearch
from stoqlib.gui.dialogs.initialstockdialog import InitialStockDialog
from stoqlib.gui.dialogs.productstockdetails import ProductStockHistoryDialog
from stoqlib.gui.dialogs.productimage import ProductImageViewer
from stoqlib.reporting.product import SimpleProductReport

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext


class StockApp(SearchableAppWindow):
    app_name = _('Stock')
    app_icon_name = 'stoq-stock-app'
    gladefile = "stock"
    search_table = ProductFullStockView
    search_labels = _('Matching:')
    klist_selection_mode = gtk.SELECTION_MULTIPLE
    pixbuf_converter = converter.get_converter(gtk.gdk.Pixbuf)

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self.check_open_inventory()
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
        return [SearchColumn('code', title=_('Code'), sorted=True,
                             sort_func=sort_sellable_code,
                             data_type=str, width=100),
                SearchColumn('barcode', title=_("Barcode"), data_type=str,
                             width=100),
                SearchColumn('category_description', title=_("Category"),
                             data_type=str, width=100, visible=False),
                SearchColumn('description', title=_("Description"),
                             data_type=str, expand=True,
                             ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('location', title=_("Location"), data_type=str,
                             width=100, visible=False),
                SearchColumn('stock', title=_('Quantity'),
                             data_type=decimal.Decimal, width=80),
                SearchColumn('unit', title=_("Unit"), data_type=str,
                             width=40),
                Column('product.has_image', title=_('Picture'),
                       data_type=bool),
                 ]

    def query(self, query, having, conn):
        branch = self.branch_filter.get_state().value
        return self.search_table.select_by_branch(query, branch,
                                                  having=having,
                                                  connection=conn)

    def set_open_inventory(self):
        self.transfer_action.set_sensitive(False)
        self.receive_action.set_sensitive(False)
        self.initial_stock_action.set_sensitive(False)
        self.stock_decrease_action.set_sensitive(False)
        self.NewLoan.set_sensitive(False)
        self.CloseLoan.set_sensitive(False)

    #
    # Private API
    #

    def _get_branches(self):
        items = [(b.person.name, b)
                  for b in Person.iselect(IBranch, connection=self.conn)]
        if not items:
            raise DatabaseInconsistency('You should have at least one '
                                        'branch on your database.'
                                        'Found zero')
        items.insert(0, [_('All branches'), None])
        return items

    def _setup_widgets(self):
        self.image_viewer = None
        space = gtk.EventBox()
        space.show()
        self.button_box.pack_start(space)

        self.image = gtk.Image()

        button = gtk.Button()
        button.set_size_request(74, 64)
        button.set_image(self.image)
        button.set_relief(gtk.RELIEF_NONE)
        button.show()
        button.connect('clicked', self._on_image_button__clicked)
        self.button_box.pack_start(button, False, False)
        self.image_button = button

        self.search.set_summary_label(column='stock',
                                      label=_('<b>Stock Total:</b>'),
                                      format='<b>%s</b>')

    def _update_widgets(self):
        branch = get_current_branch(self.conn)

        is_main_branch = self.branch_filter.get_state().value is branch
        has_stock = len(self.results) > 0

        selected = self.results.get_selected_rows()
        one_selected = len(selected) == 1

        pixbuf = None
        if one_selected:
            item = selected[0]
            pixbuf = self.pixbuf_converter.from_string(item.product.image)
            if self.image_viewer:
                self.image_viewer.set_product(item.product)
        if pixbuf:
            self.image.set_from_pixbuf(pixbuf)
        else:
            self.image.set_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_DIALOG)

        self.image_button.set_sensitive(one_selected)
        self.history_button.set_sensitive(one_selected and is_main_branch)
        self.print_button.set_sensitive(has_stock)
        # We need more than one branch to be able to do transfers
        # Note that 'all branches' is not a real branch
        has_branches = len(self.branch_filter.combo) > 2

        transfer_active = self.transfer_action.get_sensitive()
        self.transfer_action.set_sensitive(transfer_active and has_branches)
        self.TransferSearch.set_sensitive(has_branches)

    def _update_filter_slave(self, slave):
        self.refresh()

    def _transfer_stock(self):
        trans = new_transaction()
        model = self.run_dialog(StockTransferWizard, trans)
        finish_transaction(trans, model)
        trans.close()

    #
    # Callbacks
    #

    def on_image_viewer_closed(self, window, event):
        self.image_viewer = None

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

    def on_StockDecreaseSearch__activate(self, action):
        self.run_dialog(StockDecreaseSearch, self.conn)

    def on_PurchasedItemsSearch__activate(self, action):
        self.run_dialog(PurchasedItemsSearch, self.conn)

    def on_SearchStockItems__activate(self, action):
        self.run_dialog(ProductStockSearch, self.conn)

    def on_SearchClosedStockItems__activate(self, action):
        self.run_dialog(ProductClosedStockSearch, self.conn)

    def on_ProductHistory__activate(self, action):
        self.run_dialog(ProductSearchQuantity, self.conn)

    def on_initial_stock_action__activate(self, action):
        branch = self.branch_filter.get_state().value
        self.run_dialog(InitialStockDialog, self.conn, branch)

    def on_receiving_search_action_clicked(self, button):
        self.run_dialog(PurchaseReceivingSearch, self.conn)

    def on_stock_decrease_action__activate(self, action):
        trans = new_transaction()
        model = self.run_dialog(StockDecreaseWizard, trans)
        finish_transaction(trans, model)
        trans.close()

    def on_help_contents__activate(self, action):
        show_contents()

    def on_help_stock__activate(self, action):
        show_section('estoque-inicio')

    def on_print_button__clicked(self, button):
        branch_name = self.branch_filter.combo.get_active_text()
        self.print_report(SimpleProductReport, self.results,
                          branch_name=branch_name)

    def on_history_button__clicked(self, button):
        selected = self._klist.get_selected_rows()
        if len(selected) != 1:
            raise ValueError("You should have only one selected item at "
                             "this point")
        sellable = Sellable.get(selected[0].id, connection=self.conn)
        self.run_dialog(ProductStockHistoryDialog, self.conn, sellable,
                        branch=self.branch_filter.combo.get_selected())

    def on_toggle_picture_viewer_action_clicked(self, button):
        if self.image_viewer:
            self.image_viewer.destroy()
            self.image_viewer = None
        else:
            self.image_viewer = ProductImageViewer()
            selected = self.results.get_selected_rows()
            if len(selected):
                self.image_viewer.set_product(selected[0].product)
            self.image_viewer.toplevel.connect(
                "delete-event", self.on_image_viewer_closed)
            self.image_viewer.toplevel.set_property("visible", True)

    def _on_image_button__clicked(self, button):
        selected = self.results.get_selected_rows()
        one_selected = len(selected) == 1

        if not one_selected:
            return

        trans = new_transaction()
        product = trans.get(selected[0].product)

        model = self.run_dialog(ProductStockEditor, trans, product)
        finish_transaction(trans, model)
        trans.close()

    def on_NewLoan__activate(self, action):
        trans = new_transaction()
        model = self.run_dialog(NewLoanWizard, trans)
        finish_transaction(trans, model)
        trans.close()

    def on_CloseLoan__activate(self, action):
        trans = new_transaction()
        model = self.run_dialog(CloseLoanWizard, trans)
        finish_transaction(trans, model)
        trans.close()

    def on_SearchLoan__activate(self, action):
        self.run_dialog(LoanSearch, self.conn)

    def on_SearchLoanItems__activate(self, action):
        self.run_dialog(LoanItemSearch, self.conn)
