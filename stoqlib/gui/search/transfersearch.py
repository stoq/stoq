# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
""" Search dialogs for transfer order"""

import datetime
from decimal import Decimal

import gtk
from kiwi.ui.objectlist import Column
from storm.expr import And, Or, Not

from stoqlib.api import api
from stoqlib.domain.transfer import (TransferOrder, TransferOrderView,
                                     TransferItemView)
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.search.searchfilters import ComboSearchFilter
from stoqlib.gui.dialogs.transferorderdialog import TransferOrderDetailsDialog
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.transfer import TransferOrderReport, TransferItemReport

_ = stoqlib_gettext


class TransferOrderSearch(SearchDialog):
    title = _(u"Transfer Order Search")
    size = (750, 500)
    search_spec = TransferOrderView
    report_class = TransferOrderReport
    selection_mode = gtk.SELECTION_MULTIPLE

    def __init__(self, store):
        SearchDialog.__init__(self, store)
        self._setup_widgets()

    def _show_transfer_order_details(self, order_view):
        transfer_order = order_view.transfer_order
        run_dialog(TransferOrderDetailsDialog, self, self.store,
                   transfer_order)

    def _setup_widgets(self):
        self.results.connect('row_activated', self.on_row_activated)
        self.update_widgets()

    def _get_status_values(self):
        items = [(str(value), key) for key, value in
                 TransferOrder.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    #
    # SearchDialog Hooks
    #

    def update_widgets(self):
        orders = self.results.get_selected_rows()
        has_one_selected = len(orders) == 1
        self.set_details_button_sensitive(has_one_selected)
        self.set_print_button_sensitive(has_one_selected)

    def create_filters(self):
        self.set_text_field_columns(['source_branch_name',
                                     'destination_branch_name',
                                     'identifier_str'])

        # Date
        self.date_filter = DateSearchFilter(_('Date:'))
        self.add_filter(self.date_filter, columns=['open_date',
                                                   'finish_date'])

        # Status
        self.status_filter = ComboSearchFilter(_('With status:'),
                                               self._get_status_options())
        self.status_filter.select('pending')
        executer = self.search.get_query_executer()
        executer.add_filter_query_callback(self.status_filter,
                                           self._get_status_query)
        self.add_filter(self.status_filter, position=SearchFilterPosition.TOP)

    def _get_status_options(self):
        return [
            (_('All transfers'), None),
            (_('Pending receive'), 'pending'),
            (_('Received'), 'received'),
            (_('Sent'), 'sent'),
            (_('Cancelled'), 'cancelled'),
        ]

    def _get_status_query(self, state):
        current_branch = api.get_current_branch(self.store)
        if state.value == 'pending':
            return And(TransferOrder.status == TransferOrder.STATUS_SENT,
                       TransferOrder.destination_branch_id == current_branch.id)
        elif state.value == 'received':
            return And(TransferOrder.status == TransferOrder.STATUS_RECEIVED,
                       TransferOrder.destination_branch_id == current_branch.id)
        elif state.value == 'sent':
            return And(TransferOrder.source_branch_id == current_branch.id,
                       Not(TransferOrder.status == TransferOrder.STATUS_CANCELLED))
        elif state.value == 'cancelled':
            return And(TransferOrder.status == TransferOrder.STATUS_CANCELLED,
                       TransferOrder.source_branch_id == current_branch.id)
        else:
            return Or(TransferOrder.source_branch_id == current_branch.id,
                      TransferOrder.destination_branch_id == current_branch.id)

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Transfer #')),
                SearchColumn('transfer_order.status_str', _('Status'), data_type=str,
                             valid_values=self._get_status_values(),
                             search_attribute='status', width=100),
                SearchColumn('open_date', _('Open date'),
                             data_type=datetime.date, sorted=True, width=100),
                SearchColumn('finish_date', _('Finish Date'),
                             data_type=datetime.date, width=100,
                             visible=False),
                SearchColumn('source_branch_name', _('Source'),
                             data_type=str, expand=True),
                SearchColumn('destination_branch_name', _('Destination'),
                             data_type=str, width=220),
                Column('total_items', _('Items'), data_type=Decimal,
                       format_func=format_quantity, width=110)]

    #
    # Callbacks
    #

    def on_row_activated(self, klist, view):
        self._show_transfer_order_details(view)

    def on_details_button_clicked(self, button):
        self._show_transfer_order_details(self.results.get_selected_rows()[0])


class TransferItemSearch(TransferOrderSearch):
    title = _(u"Transfer Item Search")
    size = (750, 500)
    search_spec = TransferItemView
    report_class = TransferItemReport

    def _show_transfer_order_details(self, order_view):
        transfer_order = order_view.transfer_order
        run_dialog(TransferOrderDetailsDialog, self, self.store,
                   transfer_order)

    def get_columns(self):
        return [IdentifierColumn('identifier'),
                SearchColumn('finish_date', _('Finish Date'),
                             data_type=datetime.date, width=100,
                             visible=False),
                SearchColumn('item_description', _('Item'), data_type=str),
                SearchColumn('item_quantity', _('Quantity'), data_type=Decimal,
                             format_func=format_quantity, width=110),
                SearchColumn('source_branch_name', _('Source'),
                             data_type=str, expand=True),
                SearchColumn('destination_branch_name', _('Destination'),
                             data_type=str, width=220),
                Column('transfer_order.status_str', _('Status'), data_type=str,
                       width=100, visible=False),
                Column('open_date', _('Open date'),
                       data_type=datetime.date, sorted=True, width=100)]
