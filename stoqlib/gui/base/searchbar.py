# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006, 2007 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##

""" Toolbar to facilitate searching"""

import gtk
import gobject
from kiwi.log import Logger
from kiwi.utils import gsignal
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.objectlist import Column
from sqlobject.sqlbuilder import LIKE, AND, func, OR
from sqlobject.col import SOUnicodeCol, SOIntCol, SODateTimeCol, SODateCol
from zope.interface import implements

from stoqlib.database.columns import AbstractDecimalCol, SOPriceCol
from stoqlib.gui.base.columns import FacetColumn, ForeignKeyColumn
from stoqlib.gui.base.dialogs import print_report
from stoqlib.gui.interfaces import ISearchBarEntrySlave
from stoqlib.lib.component import Adapter
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam

_ = stoqlib_gettext

log = Logger("stoqlib.gui.searchbar")

#
# Slaves for search dialogs.
#

class _SearchBarEntry(GladeSlaveDelegate):

    implements(ISearchBarEntrySlave)

    gladefile = 'SearchBarEntry'
    gsignal('selected')

    SEARCH_ICON_SIZE = gtk.ICON_SIZE_LARGE_TOOLBAR
    ANIMATE_TIMEOUT = 200

    def __init__(self, filter_slave=None):
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self.search_icon.set_from_stock("stoq-searchtool-icon1",
                                        self.SEARCH_ICON_SIZE)
        if filter_slave:
            self.attach_slave('filter_area', filter_slave)
        self.search_icon.hide()
        self.search_entry.grab_focus()

    def set_search_label(self, search_entry_lbl, date_search_lbl=None):
        self.search_label.set_text(search_entry_lbl)

    def get_search_string(self):
        return self.search_entry.get_text()

    def set_search_string(self, search_str):
        return self.search_entry.set_text(search_str)

    def clear(self):
        self.search_entry.set_text('')

    def get_slave(self):
        return self

    def get_extra_queries(self):
        return []

    #
    # Kiwi callbacks
    #

    def on_search_button__clicked(self, button):
        self.emit('selected')

    def on_search_entry__activate(self, entry):
        self.emit('selected')

    #
    # Animation
    #

    def _animate_search_icon(self):
        stocklist = ["stoq-searchtool-icon2",
                     "stoq-searchtool-icon3",
                     "stoq-searchtool-icon4",
                     "stoq-searchtool-icon1"]

        while True:
            for stock in stocklist:
                self.search_icon.set_from_stock(stock, self.SEARCH_ICON_SIZE)
                yield True

        yield False

    def start_animation(self):
        self.search_button.hide()
        self.search_icon.show()
        self._animate_search_icon_id = \
            gobject.timeout_add(self.ANIMATE_TIMEOUT,
                                self._animate_search_icon().next)

    def stop_animation(self):
        self.search_button.show()
        if self._animate_search_icon_id == -1:
            log.warn("Search icon animation hasn't started")
        gobject.source_remove(self._animate_search_icon_id)
        self.search_icon.hide()


class _DateInterval:
    """A basic class for a range of dates used by DateSearchSlave as the
    model object
    """
    start_date = None
    end_date = None

class _DateSearchSlave(GladeSlaveDelegate):

    implements(ISearchBarEntrySlave)

    gladefile = 'DateSearchSlave'
    proxy_widgets = ('start_date',
                     'end_date')
    gsignal('start-date-selected')
    gsignal('end-date-selected')

    def __init__(self, filter_slave, fields):
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        # As we want to use kiwi validators with date fields we need to set
        # proxies here.
        self._model = _DateInterval()
        self._fields = fields
        self.add_proxy(self._model, self.proxy_widgets)
        self._slave = _SearchBarEntry(filter_slave)
        self.attach_slave('searchentry_holder', self._slave)
        self._update_view()

    def _update_view(self):
        enable_dates = self.date_check.get_active()
        self.start_date.set_sensitive(enable_dates)
        self.end_date.set_sensitive(enable_dates)

    def get_slave(self):
        return self._slave

    def get_search_string(self):
        return self._slave.get_search_string()

    def set_search_string(self, search_str):
        return self._slave.set_search_string(search_str)

    def set_search_label(self, search_entry_lbl, date_search_lbl=None):
        self._slave.set_search_label(search_entry_lbl)
        if date_search_lbl is None:
            date_search_lbl = ''
        self.search_label.set_text(date_search_lbl)

    def get_extra_queries(self):
        start_date = self._model.start_date
        end_date = self._model.end_date

        queries = []
        for field_name, table in self._fields:
            table_field = getattr(table.q, field_name)
            # Today -> DATE(field) = DATE(TODAY())
            if self.today_check.get_active():
                queries.append(
                    func.DATE(table_field) == func.DATE(func.NOW()))
            # Date -> field >= DATE(start) or
            #         field >= DATE(start) AND field <= DATE(end) or
            #         field <= DATE(end)
            elif self.date_check.get_active():
                if start_date:
                    queries.append(table_field >= func.DATE(start_date))
                if end_date:
                    queries.append(table_field <= func.DATE(end_date))
            # Any date -> Nothing
            elif self.anytime_check.get_active():
                pass
            else:
                raise AssertionError

        return queries

    def start_animation(self):
        self._slave.start_animation()

    def stop_animation(self):
        self._slave.stop_animation()

    def clear(self):
        self.start_date.set_text('')
        self.end_date.set_text('')

    #
    # Kiwi callbacks
    #

    """ today callbacks """
    def on_today_check__toggled(self, *args):
        self._update_view()

    def on_anytime_check__toggled(self, *args):
        self._update_view()

    def on_date_check__toggled(self, *args):
        self._update_view()

    def on_start_date__activate(self, *args):
        self.emit('start-date-selected')

    def on_end_date__activate(self, *args):
        self.emit('end-date-selected')


class SearchBar(GladeSlaveDelegate):
    """A portable search bar slave for dialogs and applications"""

    gladefile = 'SearchBarHolder'

    gsignal('before-search-activate')
    gsignal('search-activate', object)

    def __init__(self, conn, table_type, columns=None, query_args=None,
                 search_callback=None, filter_slave=None,
                 searching_by_date=False):
        """
        @param conn: a sqlobject Transaction instance
        @param table_type: an AbstractModel subclass
        @param columns: a list of instances inherited by kiwi Column
        @param query_args: a list of strings that are argument which will be
                           sent to the sqlobject select method
        @param search_callback:
        @param filter_slave:
        @param searching_by_date:
        """

        self._conn = conn
        self._columns = columns
        self._table = table_type
        self._query_args = query_args
        self._slave_callback = search_callback
        self._filter_slave = filter_slave
        self._searching_by_date = searching_by_date
        self._animate_search_icon_id = -1
        self._extra_query_callback = None
        self._blocked_results_counter = None
        self._result_strings = None
        self._int_fields = []
        self._decimal_fields = []
        self._str_fields = []
        self._dtime_fields = []
        self.max_search_results = sysparam(conn).MAX_SEARCH_RESULTS

        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self.search_results_label.set_text('')
        self.search_results_label.set_size('small')

        if searching_by_date:
            slave = _DateSearchSlave(filter_slave, self._dtime_fields)
            slave.connect('start-date-selected',
                                self._on_date_search__start_date_selected)
            slave.connect('end-date-selected',
                                self._on_date_search__end_date_selected)
        else:
            slave = _SearchBarEntry(filter_slave)
        entry_slave = slave.get_slave()
        entry_slave.connect('selected', self._on_search_entry__selected)
        self.attach_slave('place_holder', slave)
        self._slave = slave

        self.split_field_types()

    # Callbacks

    def _on_date_search__start_date_selected(self, datesearch):
        self.search_items()

    def _on_date_search__end_date_selected(self, datesearch):
        self.search_items()

    def _on_search_entry__selected(self, searchentry):
        self.search_items()

    #
    # Preparing query fields and groups
    #

    def _set_field_types(self, columns, attributes, table):
        for column in table.sqlmeta.columns.values():
            if not column.origName in attributes:
                continue
            value = (column.name, table)
            if (isinstance(column, SOUnicodeCol)
                and value not in self._str_fields):
                self._str_fields.append(value)
            elif (isinstance(column, SOIntCol)
                  and value not in self._int_fields):
                self._int_fields.append(value)
            elif (isinstance(column, (SOPriceCol, AbstractDecimalCol))
                  and value not in self._decimal_fields):
                self._decimal_fields.append(value)
            elif (isinstance(column, (SODateTimeCol, SODateCol))
                  and value not in self._dtime_fields):
                self._dtime_fields.append(value)

    def split_field_types(self):
         # We may have (eg DateSearchSlave) references to these lists, avoid
         # replacing them with a new list/reference.
        self._int_fields[:] = []
        self._decimal_fields[:] = []
        self._str_fields[:] = []
        self._dtime_fields[:] = []
        if not self._columns:
            return

        attributes = [c.attribute for c in self._columns]

        # Searching by id fields is evil, avoid it.
        if 'id' in attributes:
            raise ValueError('Private field id should not be added to '
                             'the search list')

        for k_column in self._columns:
            if isinstance(k_column, FacetColumn):
                if issubclass(self._table, Adapter):
                    table = self._table
                else:
                    iface = k_column.get_iface()
                    table = self._table.getAdapterClass(iface)
            elif isinstance(k_column, ForeignKeyColumn):
                table = k_column._table
            elif isinstance(k_column, Column):
                table = self._table
            else:
                raise TypeError('Invalid column type %s' % type(k_column))

            columns = table.sqlmeta.columns.values()
            self._set_field_types(columns, attributes, table)
            parent_class = table.sqlmeta.parentClass
            if parent_class:
                columns = parent_class.sqlmeta.columns.values()
                self._set_field_types(columns, attributes, parent_class)

    def _set_query_str(self, search_str, query):
        search_str = '%%%s%%' % search_str.upper()
        for field_name, table in self._str_fields:
            table_field = getattr(table.q, field_name)
            q = LIKE(func.UPPER(table_field), search_str)
            query.append(q)

    def _set_query_float(self, search_str, query):
        for field_name, table in self._decimal_fields:
            table_field = getattr(table.q, field_name)
            q = table_field == search_str
            query.append(q)

    def _set_query_int(self, search_str, query):
        for field_name, table in self._int_fields:
            table_field = getattr(table.q, field_name)
            q = table_field == search_str
            query.append(q)

    #
    # Building query
    #

    def _build_query(self, search_str):
        """Here we build queries after check the search string type.
        Queries are always optimized for field types to avoid database
        input syntax errors and also make smart searches.

        @param search_str: the string we are trying to find in the database
        @param search_dates: a tuple with two datetime.datetime instances
                             meaning a 'start date' and 'end date'
        """
        query = []
        if search_str:
            # Do the try/except separated from the set_query_* calls to avoid
            # catch too ValueError:s inside the function calls
            try:
                value = int(search_str)
            except ValueError:
                try:
                    value = float(search_str)
                except ValueError:
                    value = search_str

            if isinstance(value, int):
                self._set_query_int(value, query)
            elif isinstance(value, float):
                self._set_query_float(value, query)
            else:
                # Instead of checking for another type, perform later a
                # query for string fields and for any search string.
                pass
            self._set_query_str(search_str, query)

        if not query:
            if self._columns:
                columns = [c.attribute for c in self._columns]
            else:
                columns = '(not defined)'
            msg = ("There is no query for the search bar. Probably the "
                   "object type you are query on doesn't have attributes "
                   "matching with the columns argument. Got table %s and "
                   "column attributes %s" % (self._table, columns))
            raise ValueError(msg)
        query = OR(*query)
        return query

    def _run_query(self):
        # Performing search

        queries = []
        if self._extra_query_callback:
            query = self._extra_query_callback()
            if query:
                queries.append(query)

        search_str = self._slave.get_search_string()
        if search_str:
            queries.append(self._build_query(search_str))

        queries.extend(self._slave.get_extra_queries())

        kwargs = {'connection': self._conn}
        if self._query_args:
            for keyword in ['connection', 'clauseTables', 'distinct']:
                if keyword in self._query_args:
                    raise AssertionError('Invalid query argument %s' % keyword)
            kwargs.update(self._query_args)
        kwargs['distinct'] = True

        self.emit('before-search-activate')

        search_results = self._table.select(AND(*queries), **kwargs)

        total = search_results.count()
        if total > self.max_search_results:
            self._blocked_results_counter = total - self.max_search_results
        else:
            self._blocked_results_counter = 0
        results = search_results[:self.max_search_results]

        if not self._result_strings:
            self._result_strings = _('result'), _('results')
            log.warn('You must define result strings before performing '
                     'searches in the SearchBar')

        msg = self._get_search_results_msg(total, self.max_search_results)
        self.search_results_label.set_text(msg)

        # Since SQLObject doesn't support distinct-counting of sliced
        # objects we need to send here a list instead of a SearchResults
        if not isinstance(results, list):
            results = list(results)
        self.emit('search-activate', list(results))

    def _get_search_results_msg(self, search_total, max_results):
        singular_str, plural_str = self._result_strings
        if search_total == 1:
            msg = '%d %s' % (search_total, singular_str)
        elif search_total > max_results:
            msg = _('%d of %d %s shown') % (max_results, search_total,
                                            plural_str)
        elif search_total > 1:
            msg = '%d %s' % (search_total, plural_str)
        else:
            msg = ''
        return msg

    #
    # Public API
    #

    def clear(self):
        self._slave.clear()
        self.search_results_label.set_text('')

    def set_searchtable(self, search_table):
        self._table = search_table
        self.split_field_types()

    def set_columns(self, columns):
        self._columns = columns
        self.split_field_types()

    def register_extra_query_callback(self, query):
        """Register an extra query that will be added in the main query of
        SearchBar

        @param query: a sqlbuilder query
        """
        self._extra_query_callback = query

    def set_focus(self):
        if self._searching_by_date:
            self._slave.get_slave().search_entry.grab_focus()
        else:
            self._slave.search_entry.grab_focus()

    def set_result_strings(self, singular_form, plural_form):
        """This method defines strings to be used in the
        search_results_label of _SearchBarEntry class.
        """
        self._result_strings = singular_form, plural_form

    def set_searchbar_labels(self, search_entry_lbl, date_search_lbl=None):
        if self._searching_by_date:
            self._slave.set_search_label(search_entry_lbl, date_search_lbl)
        else:
            self._slave.set_search_label(search_entry_lbl)

    def search_items(self, *args):
        self._slave.start_animation()
        if self._slave_callback:
            # Perform an alternative search as desired
            self._slave_callback()
        else:
            self._run_query()
        self._slave.stop_animation()

    def get_search_string(self):
        return self._slave.get_search_string()

    def set_search_string(self, value):
        self._slave.set_search_string(value)

    def get_blocked_records_quantity(self):
        """ Return the number of records that were blocked in the last
        query.
        """
        return self._blocked_results_counter

    def get_filter_slave(self):
        return self._filter_slave

    # XXX: This part will be improved after bug #2205
    def print_report(self, report_class, *args, **kwargs):
        blocked_records = self.get_blocked_records_quantity()
        filter_slave = self.get_filter_slave()
        status = (filter_slave
                  and filter_slave.filter_combo.get_selected_data()
                  or None)
        if filter_slave and status != ALL_ITEMS_INDEX:
            status_name = filter_slave.filter_combo.get_selected_label()
        else:
            status_name = ""
        extra_filters = self.get_search_string()
        #start_date, end_date = self.get_search_dates()
        print_report(report_class, blocked_records=blocked_records,
                     status_name=status_name, extra_filters=extra_filters,
                     #start_date=start_date, end_date=end_date,
                     status=status, *args, **kwargs)

