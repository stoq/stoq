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
##  Author(s): Evandro Vale Miquelito   <evandro@async.com.br>
##
##
""" Search dialogs for fiscal objects """

from datetime import date

import gtk
from kiwi.ui.widgets.list import Column, ColoredColumn
from kiwi.datatypes import currency
from sqlobject.sqlbuilder import AND

from stoqlib.database.runtime import get_current_branch
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import ALL_ITEMS_INDEX, payment_value_colorize
from stoqlib.gui.base.search import SearchDialog
from stoqlib.gui.slaves.filterslave import FilterSlave
from stoqlib.domain.till import TillFiscalOperationsView, Till


_ = stoqlib_gettext


class TillFiscalOperationsSearch(SearchDialog):
    title = _(u"Till Fiscal Operations")
    table = TillFiscalOperationsView
    size = (750, 500)
    searching_by_date = True
    searchbar_labels = _(u"matching:"),
    searchbar_result_strings = _(u"fiscal operation"), _(u"fiscal operations")

    def __init__(self, conn):
        SearchDialog.__init__(self, conn)
        self.setup_summary_label('value', "<b>%s</b>" % (u"Total:"))

    #
    # SearchDialog Hooks
    #

    def get_columns(self, *args):
        return [Column('identifier', title=_('#'), width=60,
                       justify=gtk.JUSTIFY_RIGHT, format="%05d",
                       data_type=int, sorted=True),
                Column('date', title=_('Date'), width=80,
                       data_type=date, justify=gtk.JUSTIFY_RIGHT),
                Column('description', title=_('Description'),
                       data_type=str, expand=True),
                Column('station_name', title=_('Station'), data_type=str,
                       width=120),
                ColoredColumn('value', _('Value'), data_type=currency,
                       color='red', data_func=payment_value_colorize,
                       width=80)]

    def get_extra_query(self):
        branch_id = get_current_branch(self.conn).id
        base_query = self.search_table.q.branch_id == branch_id
        status = self.filter_slave.get_selected_status()
        if status == ALL_ITEMS_INDEX:
            return base_query
        return AND(base_query, TillFiscalOperationsView.q.status == status)

    def update_klist(self, *args):
        SearchDialog.update_klist(self, *args)

    def get_filter_slave(self):
        items = [(value, key) for key, value in Till.statuses.items()
                    if key != Till.STATUS_PENDING]
        items.insert(0, (_(u'Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(items, selected=Till.STATUS_OPEN)
        self.filter_slave.set_filter_label(_(u'Show entries of type'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)

