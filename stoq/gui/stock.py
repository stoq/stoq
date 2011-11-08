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
from kiwi.datatypes import converter, ValidationError
from kiwi.enums import SearchFilterPosition
from kiwi.log import Logger
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
log = Logger('stoq.gui.stock')


class StockApp(SearchableAppWindow):
    app_name = _('Stock')
    app_icon_name = 'stoq-stock-app'
    gladefile = "stock"
    search_table = ProductFullStockView
    search_labels = _('Matching:')
    pixbuf_converter = converter.get_converter(gtk.gdk.Pixbuf)

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._setup_widgets()
        self._update_widgets()

        # FIXME: Do this in application.py
        self.activate()

    #
    # Application
    #

    def create_actions(self):
        ui_string = """<ui>
      <menubar action="menubar">
        <menu action="StockMenu">
          <menuitem action="StockReceive"/>
          <menuitem action="StockTransfer"/>
          <menuitem action="StockDecrease"/>
          <menuitem action="StockInitial"/>
          <separator name="sep1"/>
          <menuitem action="StockPictureViewer"/>
          <separator name="sep2"/>
          <menuitem action="ExportCSV"/>
          <menuitem action="Quit"/>
        </menu>
        <menu action="LoanMenu">
          <menuitem action="LoanNew"/>
          <menuitem action="LoanClose"/>
          <separator/>
          <menuitem action="LoanSearch"/>
          <menuitem action="LoanSearchItems"/>
        </menu>
        <menu action="SearchMenu">
          <menuitem action="SearchPurchaseReceiving"/>
          <menuitem action="SearchProductHistory"/>
          <menuitem action="SearchTransfer"/>
          <menuitem action="SearchStockDecrease"/>
          <menuitem action="SearchPurchasedStockItems"/>
          <menuitem action="SearchStockItems"/>
          <menuitem action="SearchClosedStockItems"/>
        </menu>
      </menubar>
      <toolbar action="main_toolbar">
        <toolitem action="StockReceive"/>
        <toolitem action="StockTransfer"/>
      </toolbar>
    </ui>"""

        actions = [
            ('menubar', None, ''),

            # Stock
            ("StockMenu", None, _("_Stock")),
            ("StockReceive", 'stoq-receiving', _("_Receive..."), '<Control>r'),
            ('StockTransfer', 'gtk-convert', _('Transfer...'), '<Control>t'),
            ('StockDecrease', None, _('Decrease stock...')),
            ('StockInitial', 'gtk-go-up', _('Register initial stock...')),
            ('StockPictureViewer', None, _('Toggle picture viewer'),
             '<Control><Alt>v'),
            ('ExportCSV', gtk.STOCK_SAVE_AS, _('Export CSV...'), '<Control>F10'),
            ("Quit", gtk.STOCK_QUIT),

            # Loan
            ("LoanMenu", None, _("_Loan")),
            ("LoanNew", None, _("New loan...")),
            ("LoanClose", None, _("Close loan...")),
            ("LoanSearch", None, _("Search loans...")),
            ("LoanSearchItems", None, _("Search loan items...")),

            # Search
            ("SearchMenu", None, _("_Search")),
            ("SearchPurchaseReceiving", None, _("Received purchases..."),
             "<Control><Alt>u"),
            ("SearchProductHistory", None, _("Product history..."), "<Control><Alt>p"),
            ("SearchStockDecrease", None, _("Stock decreases...")),
            ("SearchPurchasedStockItems", None, _("Purchased items..."), "<Control><Alt>i"),
            ("SearchStockItems", None, _("Stock items..."), "<Control><Alt>s"),
            ("SearchTransfer", None, _("Transfers..."), "<Control><Alt>t"),
            ("SearchClosedStockItems", None, _("Closed stock Items..."),
             "<Control><Alt>c"),
        ]

        self.add_ui_actions(ui_string, actions)
        self.StockReceive.set_short_label(_("Receive"))
        self.StockTransfer.set_short_label(_("Transfer"))
        self.add_help_ui(_("Stock help"), 'vendas-inicio')

    def create_ui(self):
        self.menubar = self.uimanager.get_widget('/menubar')
        self.main_vbox.pack_start(self.menubar, False, False)
        self.main_vbox.reorder_child(self.menubar, 0)

        self.main_toolbar = self.uimanager.get_widget('/main_toolbar')
        self.toolbar_vbox.pack_start(self.main_toolbar, False, False)
        self.toolbar_vbox.reorder_child(self.main_toolbar, 0)

    def create_filters(self):
        self.executer.set_query(self.query)
        self.set_text_field_columns(['description'])
        self.branch_filter = ComboSearchFilter(
            _('Show by:'), self._get_branches())
        self.branch_filter.select(get_current_branch(self.conn))
        self.add_filter(self.branch_filter, position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [SearchColumn('code', title=_('Code'), sorted=True,
                             sort_func=sort_sellable_code,
                             data_type=str, width=130),
                SearchColumn('barcode', title=_("Barcode"), data_type=str,
                             width=130),
                SearchColumn('category_description', title=_("Category"),
                             data_type=str, width=100, visible=False),
                SearchColumn('description', title=_("Description"),
                             data_type=str, expand=True,
                             ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('location', title=_("Location"), data_type=str,
                             width=100, visible=False),
                SearchColumn('stock', title=_('Quantity'),
                             data_type=decimal.Decimal, width=100),
                SearchColumn('unit', title=_("Unit"), data_type=str,
                             width=40, visible=False),
                Column('product.has_image', title=_('Picture'),
                       data_type=bool, width=80),
                 ]

    def query(self, query, having, conn):
        branch = self.branch_filter.get_state().value
        return self.search_table.select_by_branch(query, branch,
                                                  having=having,
                                                  connection=conn)

    def set_open_inventory(self):
        self.set_sensitive(self._inventory_widgets, False)

    def activate(self):
        self.check_open_inventory()
        self._update_widgets()

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
        self._inventory_widgets = [self.StockTransfer, self.StockReceive,
                                   self.StockInitial, self.StockDecrease,
                                   self.LoanNew, self.LoanClose]
        self.register_sensitive_group(self._inventory_widgets,
                                      lambda: not self.has_open_inventory())

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

        item = self.results.get_selected()

        pixbuf = None
        if item:
            try:
                pixbuf = self.pixbuf_converter.from_string(item.product.image)
            except ValidationError:
                # FIXME: Find a better way of treating this. Somehow image
                #        is not valid for some user. See bug 4611
                pixbuf = None
                log.warning("It was not possible to load the image "
                            "of product %s" % item.product)

            if self.image_viewer:
                self.image_viewer.set_product(item.product)
        if pixbuf:
            self.image.set_from_pixbuf(pixbuf)
        else:
            self.image.set_from_stock('gtk-edit', gtk.ICON_SIZE_DIALOG)

        self.set_sensitive([self.image_button], bool(item))
        self.set_sensitive([self.history_button],
                           bool(item) and is_main_branch)
        self.set_sensitive([self.print_button], has_stock)
        # We need more than one branch to be able to do transfers
        # Note that 'all branches' is not a real branch
        has_branches = len(self.branch_filter.combo) > 2

        transfer_active = self.StockTransfer.get_sensitive()
        self.set_sensitive([self.StockTransfer],
                           transfer_active and has_branches)
        self.set_sensitive([self.SearchTransfer], has_branches)

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

    def on_print_button__clicked(self, button):
        branch_name = self.branch_filter.combo.get_active_text()
        self.print_report(SimpleProductReport, self.results,
                          list(self.results), branch_name=branch_name)

    def on_history_button__clicked(self, button):
        selected = self.results.get_selected()
        sellable = Sellable.get(selected.id, connection=self.conn)
        self.run_dialog(ProductStockHistoryDialog, self.conn, sellable,
                        branch=self.branch_filter.combo.get_selected())

    def _on_image_button__clicked(self, button):
        selected = self.results.get_selected()
        assert selected

        trans = new_transaction()
        product = trans.get(selected.product)

        model = self.run_dialog(ProductStockEditor, trans, product)
        finish_transaction(trans, model)
        trans.close()

    # Stock

    def on_StockReceive__activate(self, button):
        trans = new_transaction()
        model = self.run_dialog(ReceivingOrderWizard, trans)
        finish_transaction(trans, model)
        trans.close()

    def on_StockTransfer__activate(self, button):
        self._transfer_stock()

    def on_StockDecrease__activate(self, action):
        trans = new_transaction()
        model = self.run_dialog(StockDecreaseWizard, trans)
        finish_transaction(trans, model)
        trans.close()

    def on_StockInitial__activate(self, action):
        branch = self.branch_filter.get_state().value
        self.run_dialog(InitialStockDialog, self.conn, branch)

    def on_StockPictureViewer__activate(self, button):
        if self.image_viewer:
            self.image_viewer.destroy()
            self.image_viewer = None
        else:
            self.image_viewer = ProductImageViewer()
            selected = self.results.get_selected()
            if selected:
                self.image_viewer.set_product(selected.product)
            self.image_viewer.toplevel.connect(
                "delete-event", self.on_image_viewer_closed)
            self.image_viewer.toplevel.set_property("visible", True)

    # Loan

    def on_LoanNew__activate(self, action):
        trans = new_transaction()
        model = self.run_dialog(NewLoanWizard, trans)
        finish_transaction(trans, model)
        trans.close()

    def on_LoanClose__activate(self, action):
        trans = new_transaction()
        model = self.run_dialog(CloseLoanWizard, trans)
        finish_transaction(trans, model)
        trans.close()

    def on_LoanSearch__activate(self, action):
        self.run_dialog(LoanSearch, self.conn)

    def on_LoanSearchItems__activate(self, action):
        self.run_dialog(LoanItemSearch, self.conn)

    # Search

    def on_SearchPurchaseReceiving__activate(self, button):
        self.run_dialog(PurchaseReceivingSearch, self.conn)

    def on_SearchTransfer__activate(self, action):
        self.run_dialog(TransferOrderSearch, self.conn)

    def on_SearchPurchasedStockItems__activate(self, action):
        self.run_dialog(PurchasedItemsSearch, self.conn)

    def on_SearchStockItems__activate(self, action):
        self.run_dialog(ProductStockSearch, self.conn)

    def on_SearchClosedStockItems__activate(self, action):
        self.run_dialog(ProductClosedStockSearch, self.conn)

    def on_SearchProductHistory__activate(self, action):
        self.run_dialog(ProductSearchQuantity, self.conn)

    def on_SearchStockDecrease__activate(self, action):
        self.run_dialog(StockDecreaseSearch, self.conn)
