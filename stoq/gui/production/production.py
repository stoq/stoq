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
## Author(s):   George Y. Kussumoto     <george@async.com.br>
#
""" Main gui definition for production application.  """

import datetime
import gettext

import gtk

from kiwi.ui.objectlist import SearchColumn, Column
from kiwi.ui.search import ComboSearchFilter, SearchFilterPosition

from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.production import ProductionOrder
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.startproduction import StartProductionDialog
from stoqlib.gui.search.productionsearch import ProductionProductSearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.wizards.productionwizard import ProductionWizard

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext


class ProductionApp(SearchableAppWindow):
    app_name = _(u'Production')
    app_icon_name = 'stoq-production-app'
    gladefile = "production"
    search_table = ProductionOrder
    search_label = _(u'matching:')
    klist_selection_mode = gtk.SELECTION_MULTIPLE

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._update_widgets()

    def _update_widgets(self):
        selection = self.results.get_selected_rows()
        can_edit = False
        can_start = False
        if len(selection) == 1:
            selected = selection[0]
            can_edit = (selected.status == ProductionOrder.ORDER_OPENED or
                        selected.status == ProductionOrder.ORDER_WAITING)
            can_start = can_edit
        self.edit_button.set_sensitive(can_edit)
        self.MenuStartProduction.set_sensitive(can_start)
        self.ToolbarStartProduction.set_sensitive(can_start)

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

    def _start_production_order(self):
        trans = new_transaction()
        order = trans.get(self.results.get_selected_rows()[0])
        assert order is not None

        retval = run_dialog(StartProductionDialog, self, trans, order)
        finish_transaction(trans, retval)
        trans.close()

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
                             format='%04d'),
                SearchColumn('description', title=_(u'Description'),
                             data_type=str, expand=True),
                Column('responsible.person.name', title=_(u'Responsible'),
                       data_type=str, expand=True),
                SearchColumn('open_date', title=_(u'Opened'),
                             data_type=datetime.date),
                SearchColumn('closed_date', title=_(u'Closed'),
                             data_type=datetime.date),]

    #
    # Kiwi Callbacks
    #

    def on_Products__activate(self, action):
        self.run_dialog(ProductionProductSearch, self.conn)

    def on_Services__activate(self, action):
        self.run_dialog(ServiceSearch, self.conn, hide_price_column=True)

    def on_MenuNewProduction__activate(self, action):
        self._open_production_order()

    def on_MenuStartProduction__activate(self, action):
        self._start_production_order()

    def on_ToolbarNewProduction__activate(self, action):
        self._open_production_order()

    def on_ToolbarStartProduction__activate(self, action):
        self._start_production_order()

    def on_edit_button__clicked(self, widget):
        order = self.results.get_selected_rows()[0]
        assert order is not None
        self._open_production_order(order)

    def on_results__selection_changed(self, results, selected):
        self._update_widgets()
