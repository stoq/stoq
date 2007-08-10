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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Search dialogs for services """

import gtk
from kiwi.argcheck import argcheck
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.sellable import ASellable
from stoqlib.domain.service import Service, ServiceView
from stoqlib.gui.base.columns import Column
from stoqlib.gui.editors.serviceeditor import ServiceEditor
from stoqlib.gui.search.sellablesearch import SellableSearch

_ = stoqlib_gettext


class ServiceSearch(SellableSearch):
    title = _('Service Search')
    table = Service
    search_table = ServiceView
    size = (750, 450)
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
        SellableSearch.__init__(self, conn, hide_footer=hide_footer,
                                hide_toolbar=hide_toolbar,
                                selection_mode=selection_mode)

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'barcode'])
        items = [(v, k) for k, v in ASellable.statuses.items()]
        items.insert(0, (_('Any'), None))
        service_filter = ComboSearchFilter(_('Show services with status'),
                                          items)
        service_filter.select(None)
        self.executer.add_query_callback(self._get_query)
        self.add_filter(service_filter, SearchFilterPosition.TOP, ['status'])

    def get_branch(self):
        # We have not a filter for branches in this dialog and in this case
        # there is no filter for branches when getting the stocks
        return

    #
    # SearchEditor Hooks
    #

    @argcheck(ServiceView)
    def get_editor_model(self, model):
        return Service.get(model.service_id, connection=self.conn)

    def get_columns(self):
        columns = [Column('id', title=_('Code'), data_type=int, sorted=True,
                          format="%03d", width=80),
                   Column('barcode', title=_('Barcode'), data_type=str,
                          visible=True, width=120),
                   Column('description', title=_('Description'), data_type=str,
                          expand=True)]

        if not self.hide_cost_column:
            columns.append(Column('cost', _('Cost'), data_type=currency,
                           width=80))

        if not self.hide_price_column:
            columns.append(Column('price', title=_('Price'),
                                  data_type=currency, width=80))

        return columns

    def _get_query(self, states):
        return ServiceView.q.service_id != None
