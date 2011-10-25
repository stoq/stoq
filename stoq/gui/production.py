# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
#
""" Main gui definition for production application.  """

import datetime
import gettext

import gtk

from kiwi.ui.objectlist import SearchColumn, Column
from kiwi.ui.search import ComboSearchFilter, SearchFilterPosition

from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.production import ProductionOrder
from stoqlib.gui.dialogs.productiondetails import ProductionDetailsDialog
from stoqlib.gui.dialogs.productionquotedialog import ProductionQuoteDialog
from stoqlib.gui.dialogs.startproduction import StartProductionDialog
from stoqlib.gui.search.productionsearch import (ProductionProductSearch,
                                                 ProductionItemsSearch,
                                                 ProductionHistorySearch)
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.wizards.productionwizard import ProductionWizard
from stoqlib.reporting.production import ProductionReport

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext


class ProductionApp(SearchableAppWindow):

    # TODO: Change all widget.set_sensitive to self.set_sensitive([widget])

    app_name = _(u'Production')
    app_icon_name = 'stoq-production-app'
    gladefile = "production"
    search_table = ProductionOrder
    search_label = _(u'matching:')

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)

    #
    # Application
    #

    def create_actions(self):
        ui_string = """<ui>
      <menubar action="menubar">
        <menu action="ProductionMenu">
          <menuitem action="ProductionStart"/>
          <separator name="sep"/>
          <menuitem action="ProductionNew"/>
          <menuitem action="ProductionPurchaseQuote"/>
          <separator name="sep2"/>
          <menuitem action="ExportCSV"/>
          <separator name="sep3"/>
          <menuitem action="Quit"/>
        </menu>
        <menu action="SearchMenu">
          <menuitem action="SearchProduct"/>
          <menuitem action="SearchService"/>
          <menuitem action="SearchProductionItem"/>
          <menuitem action="SearchQualityAssurance"/>
          <menuitem action="SearchProductionHistory"/>
        </menu>
      </menubar>
      <toolbar action="main_toolbar">
        <toolitem action="ProductionNew"/>
        <toolitem action="ProductionPurchaseQuote"/>
        <toolitem action="SearchProductionItem"/>
      </toolbar>
    </ui>"""

        actions = [
            ('menubar', None, ''),

            # Production
            ("ProductionMenu", None, _("_Production")),
            ('ProductionNew', gtk.STOCK_NEW,
             _('New production order...'), '<Control>o'),
            ('ProductionStart', 'stoq-transfer',
             _('Start production...'), '<Control>t'),
            ('ProductionPurchaseQuote', 'stoq-purchase-app',
             _('New Purchase Quote...'),
             '<Control>p'),
            ('ExportCSV', gtk.STOCK_SAVE_AS, _('Export CSV...'), '<Control>F10'),
            ("Quit", gtk.STOCK_QUIT),

            # Search
            ("SearchMenu", None, _("_Search")),
            ("SearchProduct", None, _("Products..."), '<Control>d'),
            ("SearchService", None, _("Services..."), '<Control>s'),
            ("SearchProductionItem", 'stoq-production-app', _("Production items..."),
             '<Control>r'),
            ("SearchQualityAssurance", None, _("Quality Assurance..."),
             '<Control>a'),
            ("SearchProductionHistory", None, _("Production history..."), '<Control>h'),

        ]

        self.add_ui_actions(ui_string, actions)
        self.ProductionNew.set_short_label(_("New Production"))
        self.ProductionPurchaseQuote.set_short_label(_("Purchase"))
        self.SearchProductionItem.set_short_label(_("Search items"))
        self.add_help_ui(_("Production help"), 'producao-inicio')

    def create_ui(self):
        self.menubar = self.uimanager.get_widget('/menubar')
        self.main_vbox.pack_start(self.menubar, False, False)
        self.main_vbox.reorder_child(self.menubar, 0)

        self.main_toolbar = self.uimanager.get_widget('/main_toolbar')
        self.list_vbox.pack_start(self.main_toolbar, False, False)
        self.list_vbox.reorder_child(self.main_toolbar, 0)
        self._update_widgets()

    def _update_widgets(self):
        selected = self.results.get_selected()
        can_edit = False
        can_start = False
        if selected:
            can_edit = (selected.status == ProductionOrder.ORDER_OPENED or
                        selected.status == ProductionOrder.ORDER_WAITING)
            can_start = can_edit
        self.edit_button.set_sensitive(can_edit)
        self.ProductionStart.set_sensitive(can_start)
        self.start_production_button.set_sensitive(can_start)
        self.details_button.set_sensitive(bool(selected))

    def _get_status_values(self):
        items = [(text, value)
                 for value, text in ProductionOrder.statuses.items()]
        items.insert(0, (_(u'Any'), None))
        return items

    def _open_production_order(self, order=None):
        trans = new_transaction()
        order = trans.get(order)
        retval = self.run_dialog(ProductionWizard, trans, order)
        finish_transaction(trans, retval)
        trans.close()
        self.refresh()

    def _start_production_order(self):
        trans = new_transaction()
        order = trans.get(self.results.get_selected())
        assert order is not None

        retval = self.run_dialog(StartProductionDialog, trans, order)
        finish_transaction(trans, retval)
        trans.close()
        self.refresh()

    #
    # SearchableAppWindow
    #

    def create_filters(self):
        self.set_text_field_columns(['description',])
        self.status_filter = ComboSearchFilter(
            _(u'Show productions with status'), self._get_status_values())
        self.add_filter(self.status_filter, SearchFilterPosition.TOP, ['status'])

    def get_columns(self):
        return [SearchColumn('id', title=_(u'# '), sorted=True, data_type=int,
                             format='%04d', width=80),
                Column('status_string', title=_(u'Status'), data_type=str,
                        visible=False),
                SearchColumn('description', title=_(u'Description'),
                             data_type=str, expand=True),
                Column('responsible.person.name', title=_(u'Responsible'),
                       data_type=str, width=150),
                SearchColumn('open_date', title=_(u'Opened'),
                             data_type=datetime.date, width=80),
                SearchColumn('close_date', title=_(u'Closed'),
                             data_type=datetime.date, width=80)]

    #
    # Kiwi Callbacks
    #

    def on_start_production_button__clicked(self, widget):
        self._start_production_order()

    def on_edit_button__clicked(self, widget):
        order = self.results.get_selected()
        assert order is not None
        self._open_production_order(order)

    def on_details_button__clicked(self, widget):
        order = self.results.get_selected()
        assert order is not None
        self.run_dialog(ProductionDetailsDialog, self.conn, order)

    def on_print_button__clicked(self, widget):
        items = self.results
        self.print_report(ProductionReport, items, list(items),
                          self.status_filter.get_state().value)

    def on_results__selection_changed(self, results, selected):
        self._update_widgets()

    def on_results__has_rows(self, widget, has_rows):
        self.print_button.set_sensitive(has_rows)

    def on_results__row_activated(self, widget, order):
        self.run_dialog(ProductionDetailsDialog, self.conn, order)

    # Production

    def on_ProductionNew__activate(self, action):
        self._open_production_order()

    def on_ProductionStart__activate(self, action):
        self._start_production_order()

    def on_ProductionPurchaseQuote__activate(self, action):
        self.run_dialog(ProductionQuoteDialog, self.conn)

    # Search

    def on_SearchProduct__activate(self, action):
        self.run_dialog(ProductionProductSearch, self.conn)

    def on_SearchService__activate(self, action):
        self.run_dialog(ServiceSearch, self.conn, hide_price_column=True)

    def on_SearchProductionItem__activate(self, action):
        self.run_dialog(ProductionItemsSearch, self.conn)

    def on_SearchProductionHistory__activate(self, action):
        self.run_dialog(ProductionHistorySearch, self.conn)
