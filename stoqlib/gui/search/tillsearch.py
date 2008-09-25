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
##  Author(s): Evandro Vale Miquelito   <evandro@async.com.br>
##             Johan Dahlin             <jdahlin@async.com.br>
##
##
""" Search dialogs for fiscal objects """

import datetime

import gtk
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter, DateSearchFilter
from kiwi.ui.widgets.list import Column
from sqlobject.viewable import Viewable
from sqlobject.sqlbuilder import INNERJOINOn

from stoqlib.database.runtime import get_current_branch
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.search import SearchDialog
from stoqlib.domain.fiscal import CfopData, FiscalBookEntry
from stoqlib.domain.person import PersonAdaptToBranch
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.station import BranchStation
from stoqlib.domain.till import Till


_ = stoqlib_gettext

class TillFiscalOperationsView(Viewable):
    """Stores informations about till payment tables

    @ivar date:         the date when the entry was created
    @ivar description:  the entry description
    @ivar value:        the entry value
    @ivar station_name: the value of name branch_station name column
    """

    columns = dict(
        id=Payment.q.id,
        date=Payment.q.open_date,
        description=Payment.q.description,
        value=Payment.q.value,
        cfop=CfopData.q.code,
        station_name=BranchStation.q.name,
        branch_id=PersonAdaptToBranch.q.id,
        status=Till.q.status,
        )

    joins = [
        INNERJOINOn(None, Till,
                    Till.q.id == Payment.q.tillID),
        INNERJOINOn(None, BranchStation,
                    BranchStation.q.id == Till.q.stationID),
        INNERJOINOn(None, PersonAdaptToBranch,
                    PersonAdaptToBranch.q.id == BranchStation.q.branchID),
        INNERJOINOn(None, PaymentGroup,
                    PaymentGroup.q.id == Payment.q.groupID),
        INNERJOINOn(None, FiscalBookEntry,
                    FiscalBookEntry.q.payment_groupID == PaymentGroup.q.id),
        INNERJOINOn(None, CfopData,
                    CfopData.q.id == FiscalBookEntry.q.cfopID),
        ]


class TillFiscalOperationsSearch(SearchDialog):
    title = _(u"Till Fiscal Operations")
    table = TillFiscalOperationsView
    size = (750, 500)
    searching_by_date = True
    searchbar_labels = _(u"matching:"),
    searchbar_result_strings = _(u"fiscal operation"), _(u"fiscal operations")

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description'])
        self.executer.add_query_callback(self._get_query)

        # Status
        items = [(v, k) for k, v in Till.statuses.items()
                    if k != Till.STATUS_PENDING]
        items.insert(0, (_(u'Any'), None))
        status_filter = ComboSearchFilter(_(u'Show entries of type'), items)
        status_filter.select(Till.STATUS_OPEN)
        self.add_filter(status_filter,
                        position=SearchFilterPosition.TOP,
                        columns=['status'])

        # Date
        date_filter = DateSearchFilter(_('Date:'))
        self.add_filter(
            date_filter, columns=['date'])

    def get_columns(self, *args):
        return [Column('id', title=_('#'), width=60,
                       justify=gtk.JUSTIFY_RIGHT, format="%05d",
                       data_type=int, sorted=True),
                Column('date', title=_('Date'), width=80,
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                Column('description', title=_('Description'),
                       data_type=str, expand=True),
                Column('station_name', title=_('Station'), data_type=str,
                       width=120),
                Column('cfop', title=_(u"Cfop"), data_type=str,
                       width=100, justify=gtk.JUSTIFY_RIGHT),
                Column('value', _('Value'), data_type=currency,
                       width=80)]

    #
    # Private
    #

    def _get_query(self, state):
        branch = get_current_branch(self.conn)
        return self.search_table.q.branch_id == branch.id

