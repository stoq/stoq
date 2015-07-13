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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Search dialogs for fiscal objects """

import datetime

import gtk
from kiwi.currency import currency
from storm.expr import Join, Cast

from stoqlib.api import api
from stoqlib.enums import SearchFilterPosition
from stoqlib.database.viewable import Viewable
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.person import Branch
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import Sale
from stoqlib.domain.station import BranchStation
from stoqlib.domain.till import Till, TillEntry, TillClosedView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.tilldetails import TillDetailsDialog
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.search.searchfilters import DateSearchFilter, ComboSearchFilter
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


# FIXME Change it to stoqlib.domain.till
class TillFiscalOperationsView(Viewable):
    """Stores informations about till payment tables

    :attribute date:         the date when the entry was created
    :attribute description:  the entry description
    :attribute value:        the entry value
    :attribute station_name: the value of name branch_station name column
    """

    id = TillEntry.id
    identifier = Payment.identifier
    identifier_str = Cast(Payment.identifier, 'text')
    date = Payment.open_date
    description = Payment.description
    value = Payment.value

    cfop = CfopData.code
    station_name = BranchStation.name
    branch_id = Branch.id
    status = Till.status

    tables = [
        TillEntry,
        Join(Payment, Payment.id == TillEntry.payment_id),
        Join(Till, Till.id == TillEntry.till_id),
        Join(BranchStation, BranchStation.id == Till.station_id),
        Join(Branch, Branch.id == BranchStation.branch_id),
        Join(PaymentGroup, PaymentGroup.id == Payment.group_id),
        Join(Sale, Sale.group_id == PaymentGroup.id),
        Join(CfopData, CfopData.id == Sale.cfop_id),
    ]


class TillFiscalOperationsSearch(SearchDialog):
    title = _(u"Till Fiscal Operations")
    search_spec = TillFiscalOperationsView
    size = (750, 500)

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'identifier_str'])
        executer = self.search.get_query_executer()
        executer.add_query_callback(self._get_query)

        # Status
        items = [(v, k) for k, v in Till.statuses.items()
                 if k != Till.STATUS_PENDING]
        items.insert(0, (_(u'Any'), None))
        status_filter = ComboSearchFilter(_(u'Show entries of type'), items)
        status_filter.select(Till.STATUS_OPEN)
        self.add_filter(status_filter,
                        position=SearchFilterPosition.TOP,
                        columns=['status'])

    def get_columns(self, *args):
        return [IdentifierColumn('identifier', title=_('Payment #'), sorted=True),
                SearchColumn('date', title=_('Date'), width=100,
                             data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('description', title=_('Description'),
                             data_type=str, expand=True),
                SearchColumn('station_name', title=_('Station'), data_type=str,
                             width=120),
                SearchColumn('cfop', title=_('C.F.O.P.'), data_type=str,
                             width=100, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('value', _('Value'), data_type=currency,
                             width=80)]

    #
    # Private
    #

    def _get_query(self, state):
        branch = api.get_current_branch(self.store)
        return self.search_spec.branch_id == branch.id


class TillClosedSearch(SearchDialog):
    title = _(u"Till Search")
    search_spec = TillClosedView
    size = (750, 500)
    searching_by_date = True
    branch_filter_column = TillClosedView.branch_id

    def setup_widgets(self):
        self.update_widgets()

    def update_widgets(self):
        selected = self.get_selection()
        self.set_details_button_sensitive(bool(selected))

    def create_filters(self):
        self.set_text_field_columns(['responsible_open_name',
                                     'responsible_close_name'])
        self.date_filter = DateSearchFilter(_('Date:'))
        self.add_filter(self.date_filter, columns=['opening_date', 'closing_date'])

    def get_columns(self, *args):
        return [SearchColumn('opening_date', sorted=True, width=110,
                             title=_(u'Opening Date'), data_type=datetime.date,
                             justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('closing_date', width=110, title=_(u'Closing Date'),
                             data_type=datetime.date),
                SearchColumn('initial_cash_amount', title=_('Initial'),
                             data_type=currency),
                SearchColumn('final_cash_amount', title=_('Final'),
                             data_type=currency),
                SearchColumn('responsible_open_name', title=_('Opened by'),
                             data_type=str, expand=True),
                SearchColumn('responsible_close_name', title=_('Closed by'),
                             data_type=str, expand=True)]

    # Callbacks

    def on_details_button_clicked(self, button):
        view = self.results.get_selected()
        run_dialog(TillDetailsDialog, self, self.store, view)
