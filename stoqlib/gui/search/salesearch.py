# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
##
##
""" Search dialogs for sale objects """


from decimal import Decimal
from datetime import date

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.validators import format_quantity
from stoqlib.gui.base.search import SearchDialog
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.gui.slaves.filterslave import FilterSlave
from stoqlib.gui.slaves.saleslave import SaleListToolbar

_ = stoqlib_gettext


class SaleSearch(SearchDialog):
    title = _("Search for Sales")
    size = (750, 450)
    search_table = SaleView
    searching_by_date = True

    def __init__(self, conn):
        SearchDialog.__init__(self, conn, self.search_table,
                              title=self.title)
        self._setup_widgets()
        self._setup_slaves()

    def _setup_slaves(self):
        slave = SaleListToolbar(self.conn, self.search_bar,
                                self.klist, self)
        slave.disable_editing()
        self.attach_slave("extra_holder", slave)

    def _setup_widgets(self):
        self.search_bar.set_result_strings(_('sale'), _('sales'))
        self.search_bar.set_searchbar_labels(_('matching:'))

    #
    # SearchBar Hooks
    #

    def get_columns(self):
        return [Column('id', title=_('Number'), width=70,
                       data_type=int, sorted=True),
                Column('open_date', title=_('Date Started'), width=120,
                       data_type=date, justify=gtk.JUSTIFY_RIGHT),
                Column('client_name', title=_('Client'),
                       data_type=str, width=140),
                Column('salesperson_name', title=_('Salesperson'),
                       data_type=str, width=170, expand=True),
                Column('total_quantity', title=_('Items Quantity'),
                       data_type=Decimal, width=120,
                       format_func=format_quantity),
                Column('total', title=_('Total'), data_type=currency,
                       width=80)]

    def get_extra_query(self):
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            return SaleView.q.status == status

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        items = [(value, key) for key, value in Sale.statuses.items()]
        items.insert(0, (_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(items, selected=Sale.STATUS_CONFIRMED)
        self.filter_slave.set_filter_label(_('Show sales with status'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)
