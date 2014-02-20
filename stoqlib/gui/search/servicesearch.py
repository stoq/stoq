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
from kiwi.currency import currency
from storm.expr import Ne

from stoqlib.domain.service import Service, ServiceView
from stoqlib.enums import SearchFilterPosition
from stoqlib.lib.defaults import sort_sellable_code
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.service import ServiceReport, ServicePriceReport
from stoqlib.gui.base.gtkadds import change_button_appearance
from stoqlib.gui.editors.serviceeditor import ServiceEditor
from stoqlib.gui.search.searchcolumns import SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialogPrintSlave
from stoqlib.gui.search.sellablesearch import SellableSearch
from stoqlib.gui.utils.printing import print_report

_ = stoqlib_gettext


class ServiceSearch(SellableSearch):
    title = _('Service Search')
    search_spec = ServiceView
    editor_class = ServiceEditor
    report_class = ServiceReport
    model_list_lookup_attr = 'service_id'
    footer_ok_label = _('Add services')
    exclude_delivery_service = False

    def __init__(self, store, hide_footer=True, hide_toolbar=False,
                 double_click_confirm=False,
                 hide_cost_column=False, hide_price_column=False):
        self.hide_cost_column = hide_cost_column
        self.hide_price_column = hide_price_column
        SellableSearch.__init__(self, store, hide_footer=hide_footer,
                                hide_toolbar=hide_toolbar,
                                double_click_confirm=double_click_confirm)
        self._setup_print_slave()

    def _setup_print_slave(self):
        self._print_slave = SearchDialogPrintSlave()
        change_button_appearance(self._print_slave.print_price_button,
                                 gtk.STOCK_PRINT, _("Price table"))
        self.attach_slave('print_holder', self._print_slave)
        self._print_slave.connect('print', self.on_print_price_button_clicked)
        self._print_slave.print_price_button.set_sensitive(False)

    #
    #  SellableSearch
    #

    def create_filters(self):
        super(ServiceSearch, self).create_filters()

        executer = self.search.get_query_executer()
        executer.add_query_callback(self._get_query)
        service_filter = self.create_sellable_filter()
        self.add_filter(service_filter, SearchFilterPosition.TOP, ['status'])

    def get_editor_model(self, model):
        return self.store.get(Service, model.service_id)

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
        return Ne(ServiceView.service_id, None)

    #
    #  Callbacks
    #

    def on_print_price_button_clicked(self, button):
        print_report(ServicePriceReport, list(self.results),
                     filters=self.search.get_search_filters())

    def on_results__has_rows(self, results, obj):
        self._print_slave.print_price_button.set_sensitive(obj)
