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
from kiwi.ui.widgets.list import Column, ColoredColumn

from stoqlib.database.runtime import get_current_branch
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.gui.base.search import SearchDialog
from stoqlib.domain.till import TillFiscalOperationsView, Till


_ = stoqlib_gettext


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
                ColoredColumn('value', _('Value'), data_type=currency,
                       color='red', data_func=payment_value_colorize,
                       width=80)]

    #
    # Private
    #

    def _get_query(self, state):
        branch = get_current_branch(self.conn)
        return self.search_table.q.branch_id == branch.id

