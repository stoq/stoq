# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source
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
##
""" Implementation of basic dialogs for searching data """

import datetime

import gtk
import gobject
from kiwi.log import Logger
from kiwi.utils import gsignal
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.objectlist import Column, ObjectList
from kiwi.ui.widgets.list import SummaryLabel
from kiwi.argcheck import argcheck
from sqlobject.sresults import SelectResults
from sqlobject.dbconnection import Transaction
from sqlobject.sqlbuilder import LIKE, AND, func, OR
from sqlobject.col import SOUnicodeCol, SOIntCol, SODateTimeCol, SODateCol

from stoqlib.common import is_integer, is_float
from stoqlib.database.database import rollback_and_begin
from stoqlib.database.columns import AbstractDecimalCol, SOPriceCol
from stoqlib.gui.base.columns import FacetColumn, ForeignKeyColumn
from stoqlib.gui.base.dialogs import BasicDialog, run_dialog, print_report
from stoqlib.lib.component import Adapter
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.exceptions import DatabaseInconsistency

_ = stoqlib_gettext

log = Logger("stoqlib.search")

#
# Slaves for search dialogs.
#

class DateInterval:
    """A basic class for a range of dates used by DateSearchSlave as the
    model object
    """
    start_date = None
    end_date = None


class DateSearchSlave(GladeSlaveDelegate):
    gladefile = 'DateSearchSlave'
    proxy_widgets = ('start_date',
                     'end_date')
    gsignal('start-date-selected')
    gsignal('end-date-selected')

    def __init__(self, filter_slave=None):
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        # As we want to use kiwi validators with date fields we need to set
        # proxies here.
        self.model = DateInterval()
        self.add_proxy(self.model, self.proxy_widgets)
        self._slave = _SearchBarEntry(filter_slave)
        self.attach_slave('searchentry_holder', self._slave)
        self._update_view()

    def _update_view(self):
        enable_dates = not self.anytime_check.get_active()
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

    def get_search_dates(self):
        if self.anytime_check.get_active():
            return
        start_date = self.model.start_date
        # We need datetime.datetime instances in SearchBar and here we
        # must convert them since kiwi doesn't have support for datetime
        # widgets, only instances of type datetime.date
        if start_date:
            start_date = datetime.datetime(start_date.year,
                                           start_date.month,
                                           start_date.day)
        end_date = self.model.end_date
        if end_date:
            end_date = datetime.datetime(end_date.year,
                                         end_date.month,
                                         end_date.day)
        return start_date, end_date

    def start_animate_search_icon(self):
        self._slave.start_animate_search_icon()

    def stop_animate_search_icon(self):
        self._slave.stop_animate_search_icon()

    def clear(self):
        self.start_date.set_text('')
        self.end_date.set_text('')

    #
    # Kiwi callbacks
    #

    def on_anytime_check__toggled(self, *args):
        self._update_view()

    def on_date_check__toggled(self, *args):
        self._update_view()

    def on_start_date__activate(self, *args):
        self.emit('start-date-selected')

    def on_end_date__activate(self, *args):
        self.emit('end-date-selected')


class _SearchBarEntry(GladeSlaveDelegate):
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

    def set_search_label(self, search_lbl_text):
        self.search_label.set_text(search_lbl_text)

    def get_search_string(self):
        return self.search_entry.get_text()

    def set_search_string(self, search_str):
        return self.search_entry.set_text(search_str)

    def clear(self):
        self.search_entry.set_text('')

    #
    # Kiwi callbacks
    #

    def on_search_button__clicked(self, *args):
        self.emit('selected')

    def on_search_entry__activate(self, *args):
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

    def start_animate_search_icon(self):
        self.search_button.hide()
        self.search_icon.show()
        self._animate_search_icon_id = \
            gobject.timeout_add(self.ANIMATE_TIMEOUT,
                                self._animate_search_icon().next)

    def stop_animate_search_icon(self):
        self.search_button.show()
        if self._animate_search_icon_id == -1:
            log.warn("Search icon animation hasn't started")
        gobject.source_remove(self._animate_search_icon_id)
        self.search_icon.hide()


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

        """
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self.conn = conn
        self.max_search_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        self._animate_search_icon_id = -1
        self.search_results_label.set_text('')
        self.search_results_label.set_size('small')
        self.filter_slave = filter_slave
        if searching_by_date:
            self._slave = DateSearchSlave(filter_slave)
            entry_slave = self._slave.get_slave()
            self._slave.connect('start-date-selected',
                                self._on_date_search__start_date_selected)
            self._slave.connect('end-date-selected',
                                self._on_date_search__end_date_selected)
        else:
            self._slave = _SearchBarEntry(filter_slave)
            entry_slave = self._slave

        entry_slave.connect('selected', self._on_search_entry__selected)
        self._extra_query_callback = None
        self._filter_results_callback = None
        self._blocked_results_counter = None
        self.attach_slave('place_holder', self._slave)
        self.searching_by_date = searching_by_date
        self._result_strings = None
        self.columns = columns
        self.table_type = table_type
        self.query_args = query_args
        self._slave_callback = search_callback
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

    def _set_field_types(self, columns, attributes, table_type):
        for column in table_type.sqlmeta.columns.values():
            if not column.origName in attributes:
                continue
            value = (column.name, table_type)
            if (isinstance(column, SOUnicodeCol)
                and value not in self.str_fields):
                self.str_fields.append(value)
            elif (isinstance(column, SOIntCol)
                  and value not in self.int_fields):
                self.int_fields.append(value)
            elif (isinstance(column, (SOPriceCol, AbstractDecimalCol))
                  and value not in self.decimal_fields):
                self.decimal_fields.append(value)
            elif (isinstance(column, (SODateTimeCol, SODateCol))
                  and value not in self.dtime_fields):
                self.dtime_fields.append(value)

    def split_field_types(self):
        self.int_fields = []
        self.decimal_fields = []
        self.str_fields = []
        self.dtime_fields = []
        if not self.columns:
            return

        attributes = [c.attribute for c in self.columns]

        # Searching by id fields is evil, avoid it.
        if 'id' in attributes:
            raise ValueError('Private field id should not be added to '
                             'the search list')

        for k_column in self.columns:
            if isinstance(k_column, FacetColumn):
                if issubclass(self.table_type, Adapter):
                    table_type = self.table_type
                else:
                    iface = k_column.get_iface()
                    table_type = self.table_type.getAdapterClass(iface)
            elif isinstance(k_column, ForeignKeyColumn):
                table_type = k_column._table
            elif isinstance(k_column, Column):
                table_type = self.table_type
            else:
                raise TypeError('Invalid column type %s' % type(k_column))

            columns = table_type.sqlmeta.columns.values()
            self._set_field_types(columns, attributes, table_type)
            parent_class = table_type.sqlmeta.parentClass
            if parent_class:
                columns = parent_class.sqlmeta.columns.values()
                self._set_field_types(columns, attributes, parent_class)

    @argcheck(str, list)
    def _set_query_str(self, search_str, query):
        search_str = '%%%s%%' % search_str.upper()
        for field_name, table_type in self.str_fields:
            table_field = getattr(table_type.q, field_name)
            q = LIKE(func.UPPER(table_field), search_str)
            query.append(q)

    @argcheck(str, list)
    def _set_query_float(self, search_str, query):
        search_str = float(search_str)
        for field_name, table_type in self.decimal_fields:
            table_field = getattr(table_type.q, field_name)
            q = table_field == search_str
            query.append(q)

    @argcheck(str, list)
    def _set_query_int(self, search_str, query):
        search_str = int(search_str)
        for field_name, table_type in self.int_fields:
            table_field = getattr(table_type.q, field_name)
            q = table_field == search_str
            query.append(q)

    @argcheck(list, datetime.datetime, datetime.datetime)
    def _set_query_dates(self, query, start_date=None, end_date=None):
        for field_name, table_type in self.dtime_fields:
            table_field = getattr(table_type.q, field_name)
            q1 = q2 = None
            if start_date:
                q1 = table_field >= str(start_date)
            if end_date:
                end_date = end_date + datetime.timedelta(1)
                q2 = table_field < str(end_date)

            if q1 and q2:
                q = AND(q1, q2)
            else:
                q = q1 or q2
            query.append(q)

    #
    # Building query
    #

    @argcheck(str, tuple)
    def _build_query(self, search_str, search_dates=None):
        """Here we build queries after check the search string type.
        Queries are always optimized for field types to avoid database
        input syntax errors and also make smart searches.

        @param search_str: the string we are trying to find in the database
        @param search_dates: a tuple with two datetime.datetime instances
                             meaning a 'start date' and 'end date'
        """
        query = []
        if search_str:
            if is_integer(search_str):
                self._set_query_int(search_str, query)
            elif is_float(search_str):
                self._set_query_float(search_str, query)
            else:
                # Instead of checking for another type, perform later a
                # query for string fields and for any search string.
                pass
            self._set_query_str(search_str, query)

        if search_dates:
            arg_len = len(search_dates)
            if not arg_len == 2:
                raise ValueError('Argument search_date must have only two '
                                 'elements, got %s instead' % arg_len)
            start_date, end_date = search_dates
            self._set_query_dates(query, start_date, end_date)

        if not query:
            if self.columns:
                columns = [c.attribute for c in self.columns]
            else:
                columns = '(not defined)'
            msg = ("There is no query for the search bar. Probably the "
                   "object type you are query on doesn't have attributes "
                   "matching with the columns argument. Got table %s and "
                   "column attributes %s" % (self.table_type, columns))
            raise ValueError(msg)
        query = OR(*query)
        return query

    #
    # Performing search
    #

    def _run_query(self):
        if self._extra_query_callback:
            extra_query = self._extra_query_callback()
        else:
            extra_query = None

        search_str = self._slave.get_search_string()
        if isinstance(self._slave, DateSearchSlave):
            search_dates = self._slave.get_search_dates()
        else:
            search_dates = None

        query = None
        if search_str or search_dates:
            query = self._build_query(search_str, search_dates)
        if extra_query:
            query = query and AND(query, extra_query) or extra_query

        kwargs = {'connection': self.conn}
        if self.query_args:
            keys = ['connection', 'clauseTables', 'distinct']
            for query_arg in keys:
                msg = 'Invalid query argument %s' % query_arg
                assert not query_arg in self.query_args, msg
            kwargs.update(self.query_args)
        kwargs['distinct'] = True

        self.emit('before-search-activate')
        if query:
            search_results = self.table_type.select(query, **kwargs)
        else:
            search_results = self.table_type.select(**kwargs)

        total = search_results.count()
        if total > self.max_search_results:
            self._blocked_results_counter = total - self.max_search_results
        else:
            self._blocked_results_counter = 0
        objs = search_results[:self.max_search_results]

        if not self._result_strings:
            self._result_strings = _('result'), _('results')
            log.warn('You must define result strings before performing '
                     'searches in the SearchBar')

        msg = self._get_search_results_msg(total, self.max_search_results)
        self.search_results_label.set_text(msg)

        if self._filter_results_callback:
            results = self._filter_results_callback(objs)
        else:
            results = objs
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
        self.table_type = search_table
        self.split_field_types()

    def set_columns(self, columns):
        self.columns = columns
        self.split_field_types()

    def register_extra_query_callback(self, query):
        """Register an extra query that will be added in the main query of
        SearchBar

        @param query: a sqlbuilder query
        """
        self._extra_query_callback = query

    def register_filter_results_callback(self, callback):
        """Register a filter results callback that will be called right
        after fetching the data from database.

        @param callback: The callback must have only one argument of
                         type SelectResults or InheritableSelectResults.
                         This callback will process the results and filter
                         possible invalid data and must *always* return the
                         filtered list of objects.
        """
        self._filter_results_callback = callback

    def set_focus(self):
        if self.searching_by_date:
            self._slave.get_slave().search_entry.grab_focus()
        else:
            self._slave.search_entry.grab_focus()

    def set_result_strings(self, singular_form, plural_form):
        """This method defines strings to be used in the
        search_results_label of _SearchBarEntry class.
        """
        self._result_strings = singular_form, plural_form

    def set_searchbar_labels(self, search_entry_lbl, date_search_lbl=None):
        if self.searching_by_date:
            self._slave.set_search_label(search_entry_lbl, date_search_lbl)
        else:
            self._slave.set_search_label(search_entry_lbl)

    def search_items(self, *args):
        self._slave.start_animate_search_icon()
        if self._slave_callback:
            # Perform an alternative search as desired
            self._slave_callback()
        else:
            self._run_query()
        self._slave.stop_animate_search_icon()

    def get_search_string(self):
        return self._slave.get_search_string()

    def set_search_string(self, value):
        self._slave.set_search_string(value)

    def get_search_dates(self):
        res = (None, None)
        if self.searching_by_date:
            dates = self._slave.get_search_dates()
            if dates is not None:
                res = dates
        return res

    def get_blocked_records_quantity(self):
        """ Return the number of records that were blocked in the last
        query.
        """
        return self._blocked_results_counter

    def get_filter_slave(self):
        return self.filter_slave

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
        start_date, end_date = self.get_search_dates()
        print_report(report_class, blocked_records=blocked_records,
                     status_name=status_name, extra_filters=extra_filters,
                     start_date=start_date, end_date=end_date,
                     status=status, *args, **kwargs)

class SearchEditorToolBar(GladeSlaveDelegate):
    """ Slave for internal use of SearchEditor, offering an eventbox for a
    toolbar and managing the 'New' and 'Edit' buttons. """

    toplevel_name = 'ToolBar'
    gladefile = 'SearchEditor'
    domain = 'stoqlib'

    gsignal('edit')
    gsignal('add')

    #
    # Kiwi handlers
    #

    def on_edit_button__clicked(self, button):
        self.emit('edit')

    def on_new_button__clicked(self, button):
        self.emit('add')


class SearchDialogDetailsSlave(GladeSlaveDelegate):
    """ Slave for internal use of SearchEditor, offering an eventbox for a
    toolbar and managing the 'New' and 'Edit' buttons. """

    gladefile = 'SearchDialogDetailsSlave'

    gsignal('details')
    gsignal('print')

    #
    # Kiwi handlers
    #

    def on_details_button__clicked(self, button):
        self.emit('details')

    def on_print_button__clicked(self, button):
        self.emit('print')

#
# Base dialogs for search.
#


class SearchDialog(BasicDialog):
    """  Base class for *all* the search dialogs, responsible for the list
    construction and "Filter" and "Clear" buttons management.

    This class must be subclassed and its subclass *must* implement the methods
    'get_columns' and 'get_query_and_args' (if desired, 'get_query_and_args'
    can be implemented in the user's slave class, so SearchDialog will get its
    slave instance and call the method directly). Its subclass also must
    implement a setup_slaves method and call its equivalent base class method
    as in:

    def setup_slave(self):
        SearchDialog.setup_slaves(self)

    or then, call it in its constructor, like:

    def __init__(self, *args):
        SearchDialog.__init__(self)

    Some important parameters:
        table = the table type which we will query on to get the objects.
        searchbar_labels = labels for SearchBar entry and date fields
        searchbar_result_strings = a tuple where each item has a singular
                                   and a plural form for searchbar results
                                   label
    Important callbacks:
        on_details_button_clicked: Subclasses must define this method
                                   properly when a details dialog is
                                   needed with SearchDialog
        on_print_button_clicked: Subclasses must define this method
                                 properly when printing data is
                                 needed with SearchDialog
    """
    main_label_text = ''
    title = ''
    table = None
    search_table = None
    selection_mode = gtk.SELECTION_BROWSE
    searchbar_labels = None
    searchbar_result_strings = None
    searching_by_date = False
    size = ()

    @argcheck(Transaction, object, object, bool, basestring, int)
    def __init__(self, conn, table=None, search_table=None, hide_footer=True,
                 title='', selection_mode=None):
        self.conn = conn
        search_table = search_table or self.search_table
        table = table or self.table
        if not (table or search_table):
            raise ValueError(
                "%r must define a table or search_table attribute" % self)
        self.search_table = search_table or table
        if (selection_mode != gtk.SELECTION_BROWSE and
            selection_mode != gtk.SELECTION_MULTIPLE):
            raise ValueError('Invalid selection mode %d' % self.selection_mode)
        self.selection_mode = selection_mode or self.selection_mode

        BasicDialog.__init__(self)
        title = title or self.title
        self.summary_label = None
        BasicDialog._initialize(self, hide_footer=hide_footer,
                                main_label_text=self.main_label_text,
                                title=title, size=self.size)
        self.set_ok_label(_('Se_lect Items'))
        self.setup_slaves()

    def _sync(self, *args):
        rollback_and_begin(self.conn)

    def _check_searchbar_settings(self, value, attr_name):
        if not value:
            return False
        if not isinstance(value, tuple):
            raise TypeError("%s attribute must be of typle tuple, "
                            "got %s" % (attr_name, type(value)))
        return True

    def _setup_searchbar(self):
        columns = self.get_columns()
        query_args = self.get_query_args()
        use_dates = self.searching_by_date
        self.search_bar = SearchBar(self.conn, self.search_table,
                                    columns, query_args=query_args,
                                    filter_slave=self.get_filter_slave(),
                                    searching_by_date=use_dates)
        extra_query = self.get_extra_query
        if extra_query:
            self.search_bar.register_extra_query_callback(extra_query)
        self.search_bar.register_filter_results_callback(self.filter_results)
        self.search_bar.connect('before-search-activate', self._sync)
        self.search_bar.connect('search-activate', self.update_klist)
        if self._check_searchbar_settings(self.searchbar_result_strings,
                                          "searchbar_result_strings"):
            self.set_result_strings(*self.searchbar_result_strings)
        if self._check_searchbar_settings(self.searchbar_labels,
                                          "searchbar_labels"):
            self.set_searchbar_labels(*self.searchbar_labels)
        self.after_search_bar_created()
        self.attach_slave('header', self.search_bar)

    def _setup_klist(self):
        self.klist_vbox = gtk.VBox()
        self.klist = ObjectList(self.get_columns(), mode=self.selection_mode)
        self.klist_vbox.pack_start(self.klist)
        self.klist_vbox.show_all()
        # XXX: I think that BasicDialog must be redesigned, if so we don't
        # need this ".remove" crap
        self.main.remove(self.main_label)
        self.main.add(self.klist_vbox)
        self.klist.show()
        self.klist.connect('cell_edited', self.on_cell_edited)
        self.klist.connect('selection-changed', self.update_widgets)

    def _setup_details_slave(self):
        has_details_btn = hasattr(self, 'on_details_button_clicked')
        has_print_btn = hasattr(self, 'on_print_button_clicked')
        if not (has_details_btn or has_print_btn):
            self._details_slave = None
            return
        self._details_slave = SearchDialogDetailsSlave()
        self.attach_slave('details_holder', self._details_slave)
        if has_details_btn:
            self._details_slave.connect("details",
                                        self.on_details_button_clicked)
        else:
            self._details_slave.details_button.hide()
        if has_print_btn:
            self._details_slave.connect("print", self.on_print_button_clicked)
        else:
            self._details_slave.print_button.hide()

    #
    # Public API
    #

    def set_searchtable(self, search_table):
        self.search_table = search_table
        self.search_bar.set_searchtable(search_table)

    def set_searchbar_columns(self, columns):
        self.search_bar.set_columns(columns)

    def set_searchbar_search_string(self, search_str):
        self.search_bar.set_search_string(search_str)

    def perform_search(self):
        self.search_bar.search_items()

    def setup_summary_label(self, column_name, label_text):
        if self.summary_label is not None:
            self.klist_vbox.remove(self.summary_label)
        value_format = '<b>%s</b>'
        self.clear_klist()
        self.summary_label = SummaryLabel(klist=self.klist,
                                          column=column_name,
                                          label=label_text,
                                          value_format=value_format)
        self.summary_label.show()
        self.klist_vbox.pack_start(self.summary_label, False)

    def setup_slaves(self, **kwargs):
        self.disable_ok()
        self._setup_klist()
        self._setup_searchbar()
        self._setup_details_slave()

    @argcheck(bool)
    def set_details_button_sensitive(self, value):
        self._details_slave.details_button.set_sensitive(value)

    def get_query_args(self):
        """An optional list of SQLObject arguments for select function."""

    def get_extra_query(self):
        """An optional SQLObject.sqlbuilder query for select statement."""

    def filter_results(self, objects):
        """Call sites can implement a filter here to allow multiple selects
        for one search when it's necessary. Multiple selects are often
        much better than one super complex query."""
        return objects

    def get_filter_slave(self):
        """Returns a slave which will be used as filter by SearchBar.
        By default it returns None which means that no filter will be
        attached. Redefine this method in child when it's needed
        """
        return None

    def after_search_bar_created(self):
        """This method will be called after creating the SearchBar
        instance.  Redefine this method in child when it's needed
        """

    def on_cell_edited(self, klist, obj, attr):
        """Override this method on child when it's needed to perform some
        tasks when editing a row.
        """

    def set_searchbar_labels(self, search_entry_lbl, date_search_lbl=None):
        self.search_bar.set_searchbar_labels(search_entry_lbl,
                                             date_search_lbl)

    def set_result_strings(self, singular_form, plural_form):
        """This method defines strings to be used in the
        search_results_label for SearchBar class.
        """
        self.search_bar.set_result_strings(singular_form, plural_form)

    def get_selection(self):
        mode = self.klist.get_selection_mode()
        if mode == gtk.SELECTION_BROWSE:
            return self.klist.get_selected()
        return self.klist.get_selected_rows()

    def clear_klist(self):
        self.klist.clear()
        self.update_widgets()

    def confirm(self):
        objs = self.get_selection()
        self.retval = objs
        self.close()

    def cancel(self, *args):
        self.retval = []
        self.close()

    #
    # Hooks
    #

    def update_klist(self, slave, objs):
        """A hook called by SearchBar and instances."""
        if not objs:
            self.klist.clear()
            self.disable_ok()
            self.update_widgets()
            return

        if isinstance(objs, (list, tuple)):
            count = len(objs)
        elif isinstance(objs, SelectResults):
            count = objs.count()
        else:
            msg = 'Invalid type for result objects: Type: %s'
            raise TypeError, msg % type(objs)

        if count:
            self.klist.add_list(objs)
            objs = iter(objs)
            selected = objs.next()
            self.klist.select(selected)
            self.enable_ok()
        if self.summary_label:
            self.summary_label.update_total()
        self.update_widgets()

    def update_widgets(self, *args):
        """ Subclass can have an 'update_widgets', and this method will be
        called when a signal is emitted by 'Filter' or 'Clear' buttons and
        also when a list item is selected. """

    #
    # Specification of methods that all subclasses *must* to implement
    #

    def get_columns(self):
        raise NotImplementedError


class SearchEditor(SearchDialog):
    """ Base class for a search "editor" dialog, that offers a 'new' and
    'edit' button on the dialog footer. The 'new' and 'edit' buttons will
    call 'editor_class' sending as its parameters a new connection and the
    object to edit for 'edit' button.

    This is also a subclass of SearchDialog and the same rules are required.

    Some important parameters:
    interface = The interface which we need to apply to the objects in
                kiwi list to get adapter for the editor.
    """
    model_editor_lookup_attr = 'id'
    has_new_button = has_edit_button = True
    model_list_lookup_attr = 'id'

    def __init__(self, conn, table=None, editor_class=None, interface=None,
                 search_table=None, hide_footer=True,
                 title='', selection_mode=gtk.SELECTION_BROWSE,
                 hide_toolbar=False):
        SearchDialog.__init__(self, conn, table, search_table,
                              hide_footer=hide_footer, title=title,
                              selection_mode=selection_mode)
        self.interface = interface
        self.editor_class = editor_class or self.editor_class
        if hide_toolbar:
            self.accept_edit_data = False
            self._toolbar.get_toplevel().hide()
        else:
            if not (self.has_new_button or self.has_edit_button):
                raise ValueError("You must set hide_footer=False instead "
                                 "of disable these two attributes.")
            if not self.editor_class:
                raise ValueError('An editor_class argument is required')

            self.accept_edit_data = self.has_edit_button
            if not self.has_new_button:
                self.hide_new_button()
            if not self.has_edit_button:
                self.hide_edit_button()
        self._selected = None
        self.klist.connect('double_click', self._on_toolbar__edit)
        self.update_widgets()

    def setup_slaves(self):
        SearchDialog.setup_slaves(self)
        self._toolbar = SearchEditorToolBar()
        self.attach_slave('extra_holder', self._toolbar)
        self._toolbar.connect("edit", self._on_toolbar__edit)
        self._toolbar.connect("add", self._on_toolbar__new)

    def update_widgets(self, *args):
        self._toolbar.edit_button.set_sensitive(len(self.klist))

    def hide_edit_button(self):
        self.accept_edit_data = False
        self._toolbar.edit_button.hide()

    def hide_new_button(self):
        self._toolbar.new_button.hide()

    def update_edited_item(self, model):
        """Update the edited item to its proper type and select it on the
        list results.
        This method must be overwritten on subclasses when editors don't
        return a valid instance or when returning more than one model.
        """
        if self._selected:
            selected = self._selected
            selected.sync()
            self.klist.update(selected)
        else:
            # user just added a new instance
            selected = self.get_searchlist_model(model)
            self.klist.append(selected)
        self.klist.select(selected)

    def run(self, obj=None):
        self._selected = obj
        if obj:
            obj = self.get_editor_model(obj)
        if obj and self.interface:
            if isinstance(obj, Adapter):
                adapted = obj.get_adapted()
            else:
                adapted = obj
            obj = self.interface(adapted)
        rv = self.run_editor(obj)
        if not rv:
            rollback_and_begin(self.conn)
            return

        if self.editor_class.model_iface:
            rv = rv.get_adapted()

        self.conn.commit()
        self.update_edited_item(rv)
        self.enable_ok()

    def run_editor(self, obj):
        return run_dialog(self.editor_class, self, self.conn, obj)

    def _on_toolbar__edit(self, toolbar, obj=None):
        if not self.accept_edit_data:
            return
        if obj is None:
            msg = "There should be only one item selected. Got %s items"
            if self.klist.get_selection_mode() == gtk.SELECTION_MULTIPLE:
                obj = self.klist.get_selected_rows()
                msg = "There should be only one item selected. Got %s items"
                qty = len(obj)
                assert qty == 1, msg % qty
            else:
                obj = self.klist.get_selected()
                assert obj, msg % 0
        self.run(obj)

    def _on_toolbar__new(self, toolbar):
        self.run()

    #
    # Hooks
    #

    def get_searchlist_model(self, model):
        attr = self.model_list_lookup_attr
        query = getattr(self.search_table.q, attr) == model.id
        items = self.search_table.select(query, connection=self.conn)
        qty = items.count()
        if not qty == 1:
            raise DatabaseInconsistency("There should be one item for "
                                        "instance %r, got %d" % (model,
                                        qty))
        return items[0]

    def get_editor_model(self, model):
        """This hook must be redefined on child when changing the type of
        the model is a requirement for edit method.
        """
        return model
