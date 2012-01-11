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

from stoqlib.api import api
from stoqlib.domain.production import ProductionOrder
from stoqlib.gui.dialogs.productiondetails import ProductionDetailsDialog
from stoqlib.gui.dialogs.productionquotedialog import ProductionQuoteDialog
from stoqlib.gui.dialogs.startproduction import StartProductionDialog
from stoqlib.gui.keybindings import get_accels
from stoqlib.gui.search.productionsearch import (ProductionProductSearch,
                                                 ProductionItemsSearch,
                                                 ProductionHistorySearch)
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.wizards.productionwizard import ProductionWizard
from stoqlib.gui.stockicons import STOQ_PRODUCTION_APP
from stoqlib.reporting.production import ProductionReport

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext


class ProductionApp(SearchableAppWindow):

    app_name = _(u'Production')
    gladefile = "production"
    search_table = ProductionOrder
    search_label = _(u'matching:')
    report_table = ProductionReport
    embedded = True

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.production')
        actions = [
            ('menubar', None, ''),

            # File
            ('NewProduction', gtk.STOCK_NEW,
             _('Production order...'),
             group.get('new_production_order'),
             _('Create a new production')),
            ('ProductionPurchaseQuote', STOQ_PRODUCTION_APP,
             _('Purchase quote...'),
             group.get('new_production_quote')),

             # Production
            ('ProductionMenu', None, _('Production')),
            ('StartProduction', gtk.STOCK_CONVERT, _('Start production...'),
             group.get('production_start'),
             _('Start the selected production')),
            ('EditProduction', gtk.STOCK_EDIT, _('Edit production...'),
             group.get('production_edit'),
             _('Edit the selected production')),
            ('ProductionDetails', gtk.STOCK_INFO, _('Production details...'),
             group.get('production_details'),
            _('Show production details and register produced items')),

            # Search
            ("SearchProduct", None, _("Production products..."),
             group.get('search_production_products'),
             _("Search for production products")),
            ("SearchService", None, _("Services..."),
             group.get('search_services'),
             _("Search for services")),
            ("SearchProductionItem", STOQ_PRODUCTION_APP,
             _("Production items..."),
             group.get('search_production_items'),
             _("Search for production items")),
            ("SearchProductionHistory", None, _("Production history..."),
             group.get('search_production_history'),
             _("Search for production history")),
        ]
        self.production_ui = self.add_ui_actions("", actions,
                                                 filename="production.xml")
        self.set_help_section(_("Production help"), 'app-production')

        self.NewProduction.set_short_label(_("New Production"))
        self.ProductionPurchaseQuote.set_short_label(_("Purchase"))
        self.SearchProductionItem.set_short_label(_("Search items"))
        self.StartProduction.set_short_label(_('Start'))
        self.EditProduction.set_short_label(_('Edit'))
        self.ProductionDetails.set_short_label(_('Details'))
        self.StartProduction.props.is_important = True

    def create_ui(self):
        self.popup = self.uimanager.get_widget('/ProductionSelection')
        self.app.launcher.add_new_items([self.NewProduction,
                                         self.ProductionPurchaseQuote])
        self.app.launcher.add_search_items([
            self.SearchProduct,
            self.SearchService,
            self.SearchProductionItem,
            ])
        self.app.launcher.Print.set_tooltip(
            _("Print a report of these productions"))

    def activate(self, params):
        self.search.refresh()
        self._update_widgets()

    def deactivate(self):
        self.uimanager.remove_ui(self.production_ui)

    def new_activate(self):
        self._open_production_order()

    def search_activate(self):
        self.run_dialog(ProductionProductSearch, self.conn)

    def create_filters(self):
        self.set_text_field_columns(['description'])
        self.status_filter = ComboSearchFilter(
            _(u'Show productions with status'), self._get_status_values())
        self.add_filter(self.status_filter, SearchFilterPosition.TOP, ['status'])

    def get_columns(self):
        return [SearchColumn('id', title=_(u'# '), sorted=True, data_type=int,
                             format='%04d', width=80, order=gtk.SORT_DESCENDING),
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

    def print_report(self, *args, **kwargs):
        # ProductionReport needs a status kwarg
        kwargs['status'] = self.status_filter.get_state().value
        super(ProductionApp, self).print_report(*args, **kwargs)

    #
    # Private
    #

    def _update_widgets(self):
        selected = self.results.get_selected()
        can_edit = False
        can_start = False
        if selected:
            can_edit = (selected.status == ProductionOrder.ORDER_OPENED or
                        selected.status == ProductionOrder.ORDER_WAITING)
            can_start = can_edit
        self.set_sensitive([self.EditProduction], can_edit)
        self.set_sensitive([self.StartProduction], can_start)
        self.set_sensitive([self.ProductionDetails], bool(selected))

    def _get_status_values(self):
        items = [(text, value)
                 for value, text in ProductionOrder.statuses.items()]
        items.insert(0, (_(u'Any'), None))
        return items

    def _open_production_order(self, order=None):
        trans = api.new_transaction()
        order = trans.get(order)
        retval = self.run_dialog(ProductionWizard, trans, order)
        api.finish_transaction(trans, retval)
        trans.close()
        self.refresh()

    def _start_production_order(self):
        trans = api.new_transaction()
        order = trans.get(self.results.get_selected())
        assert order is not None

        retval = self.run_dialog(StartProductionDialog, trans, order)
        api.finish_transaction(trans, retval)
        trans.close()
        self.refresh()

    def _production_details(self):
        order = self.results.get_selected()
        assert order is not None
        trans = api.new_transaction()
        model = trans.get(order)
        self.run_dialog(ProductionDetailsDialog, trans, model)
        api.finish_transaction(trans, True)
        trans.close()

    #
    # Kiwi Callbacks
    #

    def on_EditProduction__activate(self, widget):
        order = self.results.get_selected()
        assert order is not None
        self._open_production_order(order)

    def on_ProductionDetails__activate(self, widget):
        self._production_details()

    def on_results__selection_changed(self, results, selected):
        self._update_widgets()

    def on_results__has_rows(self, widget, has_rows):
        self._update_widgets()

    def on_results__row_activated(self, widget, order):
        self._production_details()

    def on_results__right_click(self, results, result, event):
        self.popup.popup(None, None, None, event.button, event.time)

    # Production

    def on_NewProduction__activate(self, action):
        self._open_production_order()

    def on_StartProduction__activate(self, action):
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
