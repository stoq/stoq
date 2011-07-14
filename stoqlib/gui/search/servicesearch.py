# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
##
""" Search dialogs for services """

import gtk
from kiwi.argcheck import argcheck
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.objectlist import SearchColumn
from kiwi.ui.search import ComboSearchFilter

from stoqlib.lib.defaults import sort_sellable_code
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.service import Service, ServiceView
from stoqlib.reporting.service import ServiceReport, ServicePriceReport
from stoqlib.gui.base.gtkadds import change_button_appearance
from stoqlib.gui.base.search import SearchEditor, SearchDialogPrintSlave
from stoqlib.gui.editors.serviceeditor import ServiceEditor
from stoqlib.gui.printing import print_report

_ = stoqlib_gettext


class ServiceSearch(SearchEditor):
    title = _('Service Search')
    table = Service
    search_table = ServiceView
    size = (-1, 450)
    editor_class = ServiceEditor
    model_list_lookup_attr = 'service_id'
    footer_ok_label = _('Add services')
    searchbar_result_strings = (_('service'), _('services'))

    def __init__(self, conn, hide_footer=True, hide_toolbar=False,
                 selection_mode=gtk.SELECTION_BROWSE,
                 hide_cost_column=False, use_product_statuses=None,
                 hide_price_column=False):
        self.hide_cost_column = hide_cost_column
        self.hide_price_column = hide_price_column
        self.use_product_statuses = use_product_statuses
        SearchEditor.__init__(self, conn, hide_footer=hide_footer,
                              hide_toolbar=hide_toolbar,
                              selection_mode=selection_mode)
        self.set_searchbar_labels(_('matching'))
        self._setup_print_slave()

    def _setup_print_slave(self):
        self._print_slave = SearchDialogPrintSlave()
        change_button_appearance(self._print_slave.print_price_button,
                                 gtk.STOCK_PRINT, _("Price table"))
        self.attach_slave('print_holder', self._print_slave)
        self._print_slave.connect('print', self.on_print_price_button_clicked)
        self._print_slave.print_price_button.set_sensitive(False)
        self.results.connect('has-rows', self._has_rows)

    def _has_rows(self, results, obj):
        SearchEditor._has_rows(self, results, obj)
        self._print_slave.print_price_button.set_sensitive(obj)

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'barcode'])
        items = [(v, k) for k, v in Sellable.statuses.items()]
        items.insert(0, (_('Any'), None))
        service_filter = ComboSearchFilter(_('Show services'),
                                          items)
        service_filter.select(None)
        self.executer.add_query_callback(self._get_query)
        self.add_filter(service_filter, SearchFilterPosition.TOP, ['status'])

    #
    # SearchEditor Hooks
    #

    @argcheck(ServiceView)
    def get_editor_model(self, model):
        return Service.get(model.service_id, connection=self.conn)

    def get_columns(self):
        columns = [SearchColumn('code', title=_('Code'), data_type=str, sorted=True,
                                sort_func=sort_sellable_code, width=130),
                   SearchColumn('barcode', title=_('Barcode'), data_type=str,
                                visible=True, width=130),
                   SearchColumn('description', title=_('Description'),
                                data_type=str, expand=True)]

        if not self.hide_cost_column:
            columns.append(SearchColumn('cost', _('Cost'), data_type=currency,
                                         width=80))

        if not self.hide_price_column:
            columns.append(SearchColumn('price', title=_('Price'),
                                        data_type=currency, width=80))

        return columns

    def _get_query(self, states):
        return ServiceView.q.service_id != None

    def on_print_button_clicked(self, button):
        print_report(ServiceReport, self.results, list(self.results),
                     filters=self.search.get_search_filters())

    def on_print_price_button_clicked(self, button):
        print_report(ServicePriceReport, list(self.results),
                     filters=self.search.get_search_filters())
