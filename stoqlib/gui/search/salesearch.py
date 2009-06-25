# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):       Bruno Rafael Garcia      <brg@async.com.br>
##                  Johan Dahlin             <jdahlin@async.com.br>
##
##
""" Search dialogs for sale objects """


import datetime
from decimal import Decimal

import pango
import gtk
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.objectlist import SearchColumn

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import format_quantity
from stoqlib.gui.base.search import SearchDialog
from stoqlib.domain.sale import Sale, SaleView, DeliveryView
from stoqlib.gui.slaves.saleslave import SaleListToolbar

_ = stoqlib_gettext


class SaleSearch(SearchDialog):
    title = _("Search for Sales")
    size = (750, 450)
    search_table = SaleView
    searching_by_date = True

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['client_name', 'salesperson_name'])
        self.set_searchbar_labels(_('matching:'))
        items = [(value, key) for key, value in Sale.statuses.items()]
        items.insert(0, (_('Any'), None))

        status_filter = ComboSearchFilter(_('Show sales with status'), items)
        self.add_filter(status_filter, SearchFilterPosition.TOP, ['status'])

    def get_columns(self):
        return [SearchColumn('id', title=_('Number'), width=80,
                             data_type=int, sorted=True, order=gtk.SORT_DESCENDING),
                SearchColumn('open_date', title=_('Date Started'), width=90,
                             data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('client_name', title=_('Client'),
                             data_type=str, width=200,
                             ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('salesperson_name', title=_('Salesperson'),
                             data_type=str, width=200, expand=True),
                SearchColumn('total_quantity', title=_('Items'),
                             data_type=Decimal, width=60,
                             format_func=format_quantity),
                SearchColumn('total', title=_('Total'), data_type=currency,
                             width=90)]

    def setup_widgets(self):
        self._sale_toolbar = SaleListToolbar(self.conn, self.results, self)
        self._sale_toolbar.connect('sale-returned', self._on_sale__returned)
        self._sale_toolbar.update_buttons()
        self.attach_slave("extra_holder", self._sale_toolbar)
        self.results.connect(
            'selection-changed', self._on_results__selection_changed)

        self.search.set_summary_label('total', label=_(u'Total:'),
                                      format='<b>%s</b>')

    def _update_widgets(self, sale_view):
        if sale_view is None:
            return

        sale = sale_view.sale
        can_return = sale.can_return() or sale.can_cancel()
        self._sale_toolbar.return_sale_button.set_sensitive(can_return)

    #
    # Callbacks
    #

    def _on_results__selection_changed(self, results, sale_view):
        self._update_widgets(sale_view)

    def _on_sale__returned(self, slave, sale_returned):
        if sale_returned:
            self._update_widgets(self.results.get_selected())


class DeliverySearch(SearchDialog):
    title = _(u'Delivery Search')
    table = search_table = DeliveryView
    searching_by_date = True
    size = (750, 450)

    def create_filters(self):
        self.set_text_field_columns(['description',])
        self.set_searchbar_labels(_('Items matching:'))

    def get_columns(self):
        return [SearchColumn('id', title=_('# '), data_type=int, sorted=True,
                             order=gtk.SORT_DESCENDING),
                SearchColumn('description', title=_('Item'),
                             data_type=str, expand=True),
                SearchColumn('client_name', title=_('Client'),
                             data_type=str, expand=True,
                             ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('estimated_fix_date', title=_('Estimated Date'),
                             data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('completion_date', title=_('Completion Date'),
                             data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('quantity', title=_('Quantity'), data_type=Decimal,
                             format_func=format_quantity),]
