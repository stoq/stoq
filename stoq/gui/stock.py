# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
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
from stoqlib.api import api
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.domain.interfaces import IBranch
from stoqlib.domain.person import Person
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import ProductFullStockView
from stoqlib.lib.defaults import sort_sellable_code
from stoqlib.lib.message import warning
from stoqlib.gui.dialogs.initialstockdialog import InitialStockDialog
from stoqlib.gui.dialogs.productstockdetails import ProductStockHistoryDialog
from stoqlib.gui.dialogs.productimage import ProductImageViewer
from stoqlib.gui.editors.producteditor import ProductStockEditor
from stoqlib.gui.keybindings import get_accels
from stoqlib.gui.search.loansearch import LoanItemSearch, LoanSearch
from stoqlib.gui.search.receivingsearch import PurchaseReceivingSearch
from stoqlib.gui.search.productsearch import (ProductSearchQuantity,
                                              ProductStockSearch,
                                              ProductClosedStockSearch)
from stoqlib.gui.search.purchasesearch import PurchasedItemsSearch
from stoqlib.gui.search.transfersearch import TransferOrderSearch
from stoqlib.gui.search.stockdecreasesearch import StockDecreaseSearch
from stoqlib.gui.wizards.loanwizard import NewLoanWizard, CloseLoanWizard
from stoqlib.gui.wizards.receivingwizard import ReceivingOrderWizard
from stoqlib.gui.wizards.stocktransferwizard import StockTransferWizard
from stoqlib.gui.wizards.stockdecreasewizard import StockDecreaseWizard
from stoqlib.reporting.product import SimpleProductReport
from stoqlib.gui.stockicons import STOQ_RECEIVING

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext
log = Logger('stoq.gui.stock')


class StockApp(SearchableAppWindow):
    app_name = _('Stock')
    gladefile = "stock"
    search_table = ProductFullStockView
    search_labels = _('Matching:')
    report_table = SimpleProductReport
    pixbuf_converter = converter.get_converter(gtk.gdk.Pixbuf)
    embedded = True

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.stock')
        actions = [
            ("NewReceiving", STOQ_RECEIVING, _("Order _receival..."),
             group.get('new_receiving')),
            ('NewTransfer', gtk.STOCK_CONVERT, _('Transfer...'),
             group.get('transfer_product')),
            ('NewStockDecrease', None, _('Stock decrease...')),
            ('StockInitial', gtk.STOCK_GO_UP, _('Register initial stock...')),
            ("LoanNew", None, _("Loan...")),
            ("LoanClose", None, _("Close loan...")),
            ("SearchPurchaseReceiving", None, _("Received purchases..."),
             group.get('search_receiving'),
             _("Search for received purchase orders")),
            ("SearchProductHistory", None, _("Product history..."),
             group.get('search_product_history'),
             _("Search for product history")),
            ("SearchStockDecrease", None, _("Stock decreases..."), '',
             _("Search for manual stock decreases")),
            ("SearchPurchasedStockItems", None, _("Purchased items..."),
             group.get('search_purchased_stock_items'),
             _("Search for purchased items")),
            ("SearchStockItems", None, _("Stock items..."),
             group.get('search_stock_items'),
             _("Search for items on stock")),
            ("SearchTransfer", None, _("Transfers..."),
             group.get('search_transfers'),
             _("Search for stock transfers")),
            ("SearchClosedStockItems", None, _("Closed stock Items..."),
             group.get('search_closed_stock_items'),
             _("Search for closed stock items")),
            ("LoanSearch", None, _("Loans...")),
            ("LoanSearchItems", None, _("Loan items...")),
            ("ProductMenu", None, _("Product")),
            ("ProductStockHistory", gtk.STOCK_INFO, _("History..."),
             group.get('history'),
            _('Show the stock history of the selected product')),
            ("EditProduct", gtk.STOCK_EDIT, _("Edit..."),
             group.get('edit_product'),
            _("Edit the selected product, allowing you to change it's "
              "details")),
        ]
        self.stock_ui = self.add_ui_actions('', actions,
                                            filename='stock.xml')

        toggle_actions = [
            ('StockPictureViewer', None, _('Picture viewer'),
             group.get('toggle_picture_viewer')),
        ]
        self.add_ui_actions('', toggle_actions, 'ToggleActions',
                            'toggle')
        self.set_help_section(_("Stock help"), 'app-stock')

        self.NewReceiving.set_short_label(_("Receive"))
        self.NewTransfer.set_short_label(_("Transfer"))
        self.EditProduct.set_short_label(_("Edit"))
        self.ProductStockHistory.set_short_label(_("History"))
        self.EditProduct.props.is_important = True
        self.ProductStockHistory.props.is_important = True

    def create_ui(self):
        self.popup = self.uimanager.get_widget('/StockSelection')
        self.app.launcher.add_new_items([self.NewReceiving, self.NewTransfer,
                                         self.NewStockDecrease, self.LoanNew])
        self.app.launcher.add_search_items([
            self.SearchStockItems,
            self.SearchStockDecrease,
            self.SearchClosedStockItems,
            self.SearchProductHistory,
            self.SearchPurchasedStockItems,
            self.SearchTransfer,
            ])
        self.app.launcher.Print.set_tooltip(
            _("Print a report of these products"))
        self._inventory_widgets = [self.NewTransfer, self.NewReceiving,
                                   self.StockInitial, self.NewStockDecrease,
                                   self.LoanNew, self.LoanClose]
        self.register_sensitive_group(self._inventory_widgets,
                                      lambda: not self.has_open_inventory())

        self.image_viewer = None

        self.image = gtk.Image()
        self.edit_button = self.uimanager.get_widget('/toolbar/AppToolbarPH/EditProduct')
        self.edit_button.set_icon_widget(self.image)
        self.image.show()

        self.search.set_summary_label(column='stock',
                                      label=_('<b>Stock Total:</b>'),
                                      format='<b>%s</b>',
                                      parent=self.get_statusbar_message_area())

    def activate(self, params):
        self.app.launcher.NewToolItem.set_tooltip(
            _("Create a new receiving order"))
        self.app.launcher.SearchToolItem.set_tooltip(
            _("Search for stock items"))

        self.check_open_inventory()
        self._update_widgets()

    def setup_focus(self):
        self.search.refresh()

    def deactivate(self):
        self.uimanager.remove_ui(self.stock_ui)

    def new_activate(self):
        if not self.NewReceiving.get_sensitive():
            warning(_("You cannot receive a purchase with an open inventory."))
            return
        self._receive_purchase()

    def search_activate(self):
        self.run_dialog(ProductStockSearch, self.conn)

    def set_open_inventory(self):
        self.set_sensitive(self._inventory_widgets, False)

    def print_report(self, *args, **kwargs):
        # SimpleProductReport needs a branch_name kwarg
        kwargs['branch_name'] = self.branch_filter.combo.get_active_text()
        super(StockApp, self).print_report(*args, **kwargs)

    #
    # SearchableAppWindow
    #

    def create_filters(self):
        self.executer.set_query(self._query)
        self.set_text_field_columns(['description'])
        self.branch_filter = ComboSearchFilter(
            _('Show by:'), self._get_branches())
        self.branch_filter.select(api.get_current_branch(self.conn))
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

    #
    # Private API
    #

    def _query(self, query, having, conn):
        branch = self.branch_filter.get_state().value
        return self.search_table.select_by_branch(query, branch,
                                                  having=having,
                                                  connection=conn)

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
        branch = api.get_current_branch(self.conn)

        is_main_branch = self.branch_filter.get_state().value is branch
        item = self.results.get_selected()

        pixbuf = None
        if item:
            try:
                pixbuf = self.pixbuf_converter.from_string(item.product.image)
                if pixbuf:
                    # FIXME: get this icon size from settings
                    icon_size = 24
                    pixbuf = pixbuf.scale_simple(icon_size, icon_size,
                                                 gtk.gdk.INTERP_BILINEAR)
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
            self.image.set_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_LARGE_TOOLBAR)

        self.set_sensitive([self.EditProduct], bool(item))
        self.set_sensitive([self.ProductStockHistory],
                           bool(item) and is_main_branch)
        # We need more than one branch to be able to do transfers
        # Note that 'all branches' is not a real branch
        has_branches = len(self.branch_filter.combo) > 2

        transfer_active = self.NewTransfer.get_sensitive()
        self.set_sensitive([self.NewTransfer],
                           transfer_active and has_branches)
        self.set_sensitive([self.SearchTransfer], has_branches)

    def _update_filter_slave(self, slave):
        self.refresh()

    def _transfer_stock(self):
        if self.check_open_inventory():
            return
        trans = api.new_transaction()
        model = self.run_dialog(StockTransferWizard, trans)
        api.finish_transaction(trans, model)
        trans.close()
        self.search.refresh()

    def _receive_purchase(self):
        if self.check_open_inventory():
            return
        trans = api.new_transaction()
        model = self.run_dialog(ReceivingOrderWizard, trans)
        api.finish_transaction(trans, model)
        trans.close()
        self.search.refresh()

    #
    # Callbacks
    #

    def on_image_viewer_closed(self, window, event):
        self.image_viewer = None

    def on_results__has_rows(self, results, product):
        self._update_widgets()

    def on_results__selection_changed(self, results, product):
        self._update_widgets()

    def on_results__right_click(self, results, result, event):
        self.popup.popup(None, None, None, event.button, event.time)

    def on_ProductStockHistory__activate(self, button):
        selected = self.results.get_selected()
        sellable = Sellable.get(selected.id, connection=self.conn)
        self.run_dialog(ProductStockHistoryDialog, self.conn, sellable,
                        branch=self.branch_filter.combo.get_selected())

    def on_EditProduct__activate(self, button):
        selected = self.results.get_selected()
        assert selected

        trans = api.new_transaction()
        product = trans.get(selected.product)

        model = self.run_dialog(ProductStockEditor, trans, product)
        api.finish_transaction(trans, model)
        trans.close()

    # Stock

    def on_NewReceiving__activate(self, button):
        self._receive_purchase()

    def on_NewTransfer__activate(self, button):
        self._transfer_stock()

    def on_NewStockDecrease__activate(self, action):
        if self.check_open_inventory():
            return
        trans = api.new_transaction()
        model = self.run_dialog(StockDecreaseWizard, trans)
        api.finish_transaction(trans, model)
        trans.close()
        self.search.refresh()

    def on_StockInitial__activate(self, action):
        if self.check_open_inventory():
            return
        branch = self.branch_filter.get_state().value
        self.run_dialog(InitialStockDialog, self.conn, branch)
        self.search.refresh()

    def on_StockPictureViewer__activate(self, button):
        if self.image_viewer:
            self.StockPictureViewer.props.active = False
            self.image_viewer.destroy()
            self.image_viewer = None
        else:
            self.StockPictureViewer.props.active = True
            self.image_viewer = ProductImageViewer()
            selected = self.results.get_selected()
            if selected:
                self.image_viewer.set_product(selected.product)
            self.image_viewer.toplevel.connect(
                "delete-event", self.on_image_viewer_closed)
            self.image_viewer.toplevel.set_property("visible", True)

    # Loan

    def on_LoanNew__activate(self, action):
        if self.check_open_inventory():
            return
        trans = api.new_transaction()
        model = self.run_dialog(NewLoanWizard, trans)
        api.finish_transaction(trans, model)
        trans.close()
        self.search.refresh()

    def on_LoanClose__activate(self, action):
        if self.check_open_inventory():
            return
        trans = api.new_transaction()
        model = self.run_dialog(CloseLoanWizard, trans)
        api.finish_transaction(trans, model)
        trans.close()
        self.search.refresh()

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
