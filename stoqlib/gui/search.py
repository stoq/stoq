# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
gui/search.py:

    Implementation of basic dialogs for search
"""

import string
import gettext
import datetime
import warnings

import gtk
import gobject
from twisted.python.components import Adapter
from kiwi.utils import gsignal
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.widgets.list import Column
from kiwi.argcheck import argcheck
from sqlobject.sresults import SelectResults
from sqlobject.sqlbuilder import LIKE, AND, func, OR
from sqlobject.col import (SOStringCol, SOFloatCol, SOIntCol,
                           SODateTimeCol, SODateCol)

import stoqlib
from stoqlib.gui.dialogs import BasicDialog, run_dialog
from stoqlib.exceptions import _warn
from stoqlib.common import is_integer, is_float
from stoqlib.database import get_model_connection, rollback_and_begin
from stoqlib.gui.columns import FacetColumn, ForeignKeyColumn

_ = gettext.gettext


#
# Slaves for search dialogs.
#


class BaseListSlave(SlaveDelegate):
    """ Base slave for dialogs that need a Kiwi List. If the 'parent' class
    send a 'parent' argument, the method update_widgets will be called when 
    the list be selected ou double clicked. """

    gladefile = 'BaseListSlave'
    widgets = ('klist', )
    
    def __init__(self, parent=None, columns=None, objects=None):
        SlaveDelegate.__init__(self, widgets=self.widgets, 
                               gladefile=self.gladefile)

        if not columns and (not parent or not hasattr(parent, 'get_columns')):
            raise TypeError("You must supply columns via parameter of in"
                            " parent.")
        columns = columns or parent.get_columns()

        self.parent = parent
        
        self.klist.set_columns(columns)
        if objects:
            self.klist.add_list(objects)

    def update_widgets(self):
        # 'parent' argument isn't mandatory, if it's None, 'update_widgets()'
        # of parent class isn't called.
        if self.parent:
            self.parent.update_widgets()

    def on_klist__selection_changed(self, *args):
        self.update_widgets()

    def on_klist__double_click(self, *args):
        self.update_widgets()


class DateInterval:
    """A basic class for a range of dates used by DateSearchSlave as the
    model object
    """
    start_date = None
    end_date = None


class DateSearchSlave(SlaveDelegate):
    gladefile = 'DateSearchSlave'
    proxy_widgets = ('start_date',
                     'end_date')
    widgets = ('search_label',
               "anytime_check",
               "date_check") + proxy_widgets
    gsignal('startdate-activate')
    gsignal('enddate-activate')

    def __init__(self, filter_slave=None):
        SlaveDelegate.__init__(self, gladefile=self.gladefile, 
                               widgets=self.widgets)
        # As we want to use kiwi validators with date fields we need to set
        # proxies here.
        self.model = DateInterval()
        self.add_proxy(self.model, self.proxy_widgets)
        self._slave = SearchEntry(filter_slave)
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

    #
    # Kiwi callbacks
    #

    def on_anytime_check__toggled(self, *args):
        self._update_view()

    def on_date_check__toggled(self, *args):
        self._update_view()

    def on_start_date__activate(self, *args):
        self.emit('startdate-activate')

    def on_end_date__activate(self, *args):
        self.emit('enddate-activate')


class SearchEntry(SlaveDelegate):
    gladefile = 'SearchEntry'
    widgets = ('search_button',
               'search_label',
               "search_entry",
               "search_icon")
    gsignal('searchbutton-clicked')
    gsignal('searchentry-activate')

    SEARCH_ICON_SIZE = gtk.ICON_SIZE_LARGE_TOOLBAR
    ANIMATE_TIMEOUT = 200

    def __init__(self, filter_slave=None):
        SlaveDelegate.__init__(self, gladefile=self.gladefile, 
                               widgets=self.widgets)
        self.search_icon.set_from_stock("searchtool-icon1", 
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

    #
    # Kiwi callbacks
    #

    def on_search_button__clicked(self, *args):
        self.emit('searchbutton-clicked')

    def on_search_entry__activate(self, *args):
        self.emit('searchentry-activate')

    #
    # Animation
    #

    def _animate_search_icon(self):
        dir = stoqlib.__path__[0] + '/gui/pixmaps'
        stocklist = ["searchtool-icon2",
                     "searchtool-icon3",
                     "searchtool-icon4",
                     "searchtool-icon1"]
        
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
            # TODO: it's wierd that _warn method is private. Need some refactoring
            _warn("Search icon animation hasn't started")
        gobject.source_remove(self._animate_search_icon_id)
        self.search_icon.hide()


class SearchBar(SlaveDelegate):
    """ A portable search bar slave for dialogs.

    table_type  =  The table type which we want to query on.
    fields      =  A list of tuples. Each tuple has its first element as 
                   a tuple of the object column names and the second element
                   is the table type of these columns.
                   E.g: [(('name', phone_number), Person), 
                         (('street', 'number'), Address)]

    Each parent must define a hook 'update_klist(objs)' which will be 
    called after the search.
    """
    gladefile = 'SearchBarHolder'
    widgets = ('search_results_label',)
    
    def __init__(self, parent, table_type, columns=None, query_args=None, 
                 search_callback=None, filter_slave=None, 
                 searching_by_date=False):
        SlaveDelegate.__init__(self, gladefile=self.gladefile, 
                               widgets=self.widgets)
        self._animate_search_icon_id = -1
        self.parent = parent
        self.search_results_label.set_text('')
        self.search_results_label.set_size('small')
        if searching_by_date:
            self._slave = DateSearchSlave(filter_slave)
            entry_slave = self._slave.get_slave()
            self._slave.connect('startdate-activate', self.search_items)
            self._slave.connect('enddate-activate', self.search_items)
        else:
            self._slave = SearchEntry(filter_slave)
            entry_slave = self._slave

        entry_slave.connect('searchbutton-clicked', self.search_items)
        entry_slave.connect('searchentry-activate', self.search_items)
        self.attach_slave('place_holder', self._slave)
        self.searching_by_date = searching_by_date
        # Since we need to synchronize transactions each time we search for
        # objects we have to create a special transaction for the SearchBar
        self.conn = get_model_connection()
        self._result_strings = None
        self.columns = columns
        self.table_type = table_type
        self.query_args = query_args
        self._slave_callback = search_callback
        self._split_field_types()

    def set_focus(self):
        if self.searching_by_date:
            self._slave.get_slave().search_entry.grab_focus()
        else:
            self._slave.search_entry.grab_focus()

    def set_result_strings(self, singular_form, plural_form):
        """This method defines strings to be used in the
        search_results_label of SearchEntry class.
        """
        self._result_strings = singular_form, plural_form

    def set_searchbar_labels(self, search_entry_lbl, date_search_lbl=None):
        if self.searching_by_date:
            self._slave.set_search_label(search_entry_lbl, date_search_lbl)
        else:
            self._slave.set_search_label(search_entry_lbl)

    #
    # Preparing query fields and groups
    #

    def _set_field_types(self, columns, attributes, table_type):
        for column in table_type.sqlmeta.columns.values():
            if not column.origName in attributes:
                continue
            value = (column.name, table_type)
            if (isinstance(column, SOStringCol) 
                and value not in self.str_fields):
               self.str_fields.append(value)
            elif (isinstance(column, SOIntCol)
                  and value not in self.int_fields):
                 self.int_fields.append(value)
            elif (isinstance(column, SOFloatCol)
                  and value not in self.float_fields):
                 self.float_fields.append(value)
            elif (isinstance(column, (SODateTimeCol, SODateCol))
                  and value not in self.dtime_fields):
                 self.dtime_fields.append(value)

    def _split_field_types(self):
        self.int_fields = []
        self.float_fields = []
        self.str_fields = []
        self.dtime_fields = []
        if not self.columns:
            return

        attributes = [c.attribute for c in self.columns]

        # We need this check since the id field is not actually an
        # SQLObject column 
        if 'id' in attributes:
            self.int_fields.append(('id', self.table_type))
        
        for k_column in self.columns:
            if isinstance(k_column, FacetColumn):
                if issubclass(self.table_type, Adapter):
                    table_type = self.table_type
                else:
                    facet = k_column.get_facet()
                    table_type = self.table_type.getAdapterClass(facet)
            elif isinstance(k_column, ForeignKeyColumn):
                table_type = k_column._table
            elif isinstance(k_column, Column):
                table_type = self.table_type
            else:
                raise TypeError('Invalid column type %s' % type(k_column))

            columns = table_type.sqlmeta.columns.values()
            self._set_field_types(columns, attributes, table_type)
            if table_type._parentClass:
                columns = table_type._parentClass.sqlmeta.columns.values()
                self._set_field_types(columns, attributes, 
                                      table_type._parentClass)

    def _set_query_str(self, search_str, query):
        search_str = '%%%s%%' % string.upper(search_str)
        for field_name, table_type in self.str_fields:
            table_field = getattr(table_type.q, field_name) 
            q = LIKE(func.UPPER(table_field), search_str)
            query.append(q)

    def _set_query_float(self, search_str, query):
        search_str = float(search_str)
        for field_name, table_type in self.float_fields:
            table_field = getattr(table_type.q, field_name) 
            q = table_field == search_str
            query.append(q)
           
    def _set_query_int(self, search_str, query):
        search_str = int(search_str)
        for field_name, table_type in self.int_fields:
            table_field = getattr(table_type.q, field_name) 
            q = table_field == search_str
            query.append(q)

    # FIXME waiting for bug fix in kiwi, we must check the two last
    # arguments for datetime.date instead of object. This fails when setting
    # None as default value
    @argcheck(list, object, object)
    def _set_query_dates(self, query, start_date=None, end_date=None):
        values = start_date, end_date
        for value in values:
            # XXX Remove this check after kiwi bug fix in argcheck
            if value and not isinstance(value, datetime.date):
                raise ValueError('Argument for date search must be date '
                                 'or datetime, got %s instead' % 
                                 type(value))
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

    # FIXME waiting for bug fix in kiwi. argcheck should accept None for
    # search_dates argument.
    @argcheck(str, object)
    def _build_query(self, search_str, search_dates=None):
        """Here we build queries after check the search string type. 
        Queries are always optimized for field types to avoid database 
        input syntax errors and also make smart searches."""
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
        search_str = self._slave.get_search_string()
        if isinstance(self._slave, DateSearchSlave):
            search_dates = self._slave.get_search_dates()
        else:
            search_dates = None

        query = self.table_type.q._is_valid_model == True
        if search_str or search_dates:
            query = AND(query, self._build_query(search_str, search_dates))
        
        extra_query = self.parent.get_extra_query()
        if extra_query:
            query = AND(query, extra_query) 

        kwargs = {'connection': self.conn}
        if self.query_args:
            keys = ['connection', 'clauseTables', 'distinct']
            for query_arg in keys:
                msg = 'Invalid query argument %s' % query_arg
                assert not query_arg in self.query_args, msg
            kwargs.update(self.query_args)
        kwargs['distinct'] = True
        
        # Synchronizing transaction.
        # XXX Waiting for a SQLObject sync method
        rollback_and_begin(self.conn)

        if query:
            search_results = self.table_type.select(query, **kwargs)
        else:
            search_results = self.table_type.select(**kwargs)

        max_search_results = get_max_search_results()
        objs = search_results[:max_search_results]

        total = search_results.count()
        if not self._result_strings:
            self._result_strings = _('result'), _('results')
            warnings.warn('You must define result strings before performing '
                          'searches in the SearchBar')
        singular_str, plural_str = self._result_strings
        if total == 1:
            msg = '%d %s' % (total, singular_str)
        elif total > max_search_results:
            msg = _('%d of %d %s shown') % (max_search_results, total,
                                            plural_str)
        elif total > 1:
            msg = '%d %s' % (total, plural_str)
        else:
            msg = ''

        self.search_results_label.set_text(msg)
        objs = self.parent.filter_results(objs)
        # Since SQLObject doesn't support distinct-counting of sliced
        # objects we need to send here a list instead of a SearchResults
        self.parent.update_klist(list(objs))

    def close_connection(self):
        # XXX Waiting for SQLObject improvements. We need there a simple
        # method do this in a simple way.
        self.conn._connection.close()

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


class SearchEditorToolBar(SlaveDelegate):
    """ Slave for internal use of SearchEditor, offering an eventbox for a
    toolbar and managing the 'New' and 'Edit' buttons. """

    toplevel_name = 'ToolBar'
    gladefile = 'SearchEditor'
    widgets = ('new_button', 'edit_button', 'toolbar_holder')
    
    def __init__(self, parent):
        SlaveDelegate.__init__(self, toplevel_name=self.toplevel_name,
                               gladefile=self.gladefile, 
                               widgets=self.widgets)
        self.parent = parent

    #
    # Kiwi handlers
    #

    def on_edit_button__clicked(self, widget):
        self.parent.edit(widget)

    def on_new_button__clicked(self, *args):
        self.parent.new()


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
    """
    main_label_text = ''
    title = ''
    size = ()
            
    def __init__(self, table, search_table=None, parent_conn=None,
                 hide_footer=True, title='', 
                 selection_mode=gtk.SELECTION_BROWSE, 
                 searching_by_date=False):
        BasicDialog.__init__(self)
        title = title or self.title
        avaliable_modes = [gtk.SELECTION_BROWSE, gtk.SELECTION_MULTIPLE]
        if selection_mode not in avaliable_modes:
            raise ValueError('Invalid selection mode %' % selection_mode)
        self.selection_mode = selection_mode
        BasicDialog._initialize(self, hide_footer=hide_footer,
                                main_label_text=self.main_label_text, 
                                title=title, size=self.size)
        self.set_ok_label(_('Se_lect Items'))
        self.table = table
        self.search_table = search_table or self.table
        self.parent_conn = parent_conn
        self.conn = get_model_connection()
        assert self.conn
        self.searching_by_date = searching_by_date
        self.setup_slaves()

    def setup_slaves(self, **kwargs):
        self.disable_ok()
        self.klist_slave = BaseListSlave(parent=self)
        self.attach_slave('main', self.klist_slave)
        self.klist = self.klist_slave.klist
        self.klist.connect('cell_edited', self.on_cell_edited)
        # We can not change this through gazpacho because BaseListSlave 
        # can be used for some other classes which should always redefine
        # this mode
        self.klist.set_selection_mode(self.selection_mode)

        columns = self.get_columns()
        query_args = self.get_query_args()
        use_dates = self.searching_by_date
        self.search_bar = SearchBar(self, self.search_table, columns, 
                                    query_args=query_args,
                                    filter_slave=self.get_filter_slave(),
                                    searching_by_date=use_dates)
        self.after_search_bar_created()
        self.attach_slave('header', self.search_bar)

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

    def lookup_connection(self, obj, conn=None):
        table = type(obj)
        if conn:
            return table.get(obj.id, connection=conn)
        return table.get(obj.id, connection=self.parent_conn)
        
    def restore_model_connections(self, objs=None, conn=None):
        objs = objs or self.klist[:]
        if not objs:
            return 
        if isinstance(objs, list):
            retval = []
            for obj in objs[:]:
                retval.append(self.lookup_connection(obj, conn))
        else:
            retval = self.lookup_connection(objs, conn)
        return retval

    def confirm(self):
        objs = self.get_selection()
        if self.parent_conn:
            self.retval = self.restore_model_connections(objs)
        else:
            self.retval = objs
        self.close()

    def close(self):
        self.search_bar.close_connection()
        self.conn._connection.close()
        BasicDialog.close(self)

    def cancel(self, *args):
        self.retval = []
        self.close()

    #
    # Hooks
    #

    def update_klist(self, objs=None):
        """A hook called by SearchBar and BaseListSlave instances."""
        self.klist.clear()
        
        if not objs:
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
            self.klist.select(objs[0])
            self.enable_ok()
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

    def get_query_args(self):
        """An optional list of SQLObject arguments for select function."""

    def get_extra_query(self):
        """An optional SQLObject.sqlbuilder query for select statement."""

    def filter_results(self, objects):
        """Call sites can implement a filter here to allow multiple selects
        for one search when it's necessary. Multiple selects are often 
        much better than one super complex query."""
        return objects


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

    def __init__(self, table, editor_class, interface=None,
                 parent_conn=None, search_table=None, hide_footer=True,
                 title='', selection_mode=gtk.SELECTION_BROWSE,
                 searching_by_date=False):
        SearchDialog.__init__(self, table, search_table,
                              parent_conn, hide_footer=hide_footer, 
                              title=title, selection_mode=selection_mode,
                              searching_by_date=searching_by_date)
        self.interface = interface
        self.editor_class = editor_class
        self.accept_edit_data = True
        self.klist.connect('double_click', self.edit)
        self.update_widgets()

    def setup_slaves(self):
        SearchDialog.setup_slaves(self)
        self.toolbar = SearchEditorToolBar(self)
        self.attach_slave('extra_holder', self.toolbar)

    def update_widgets(self, *args):
        self.toolbar.edit_button.set_sensitive(len(self.klist))

    def hide_edit_button(self):
        self.accept_edit_data = False
        self.toolbar.edit_button.hide()

    def hide_new_button(self):
        self.toolbar.new_button.hide()

    def run(self, obj=None):
        if obj: 
            if self.interface:
                if isinstance(obj, Adapter):
                    adapted = obj.get_adapted()
                else:
                    adapted = obj
                obj = self.interface(adapted, connection=self.conn)
            else:
                obj = self.table.get(id=obj.id, connection=self.conn)
        rv = self.run_editor(obj)
        if not rv:
            self.conn.rollback()
            self.conn.begin()
            return

        self.conn.commit()
        self.search_bar.search_items()
        # Since SearchBar has its own transaction we need to bring all the
        # objects in the list back to self.conn
        objs = self.restore_model_connections(conn=self.conn)
        self.klist.clear()
        self.klist.add_list(objs)

        if self.interface and isinstance(rv, Adapter):
            # This SearchDialog has original objects in the kiwi list and
            # that's why I need to get them back here.
            rv = rv.get_adapted()
        if rv in self.klist:
            self.klist.select(rv)

    def run_editor(self, obj):
        return run_dialog(self.editor_class, self, self.conn, obj)

    def edit(self, widget, obj=None):
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
        obj = self.get_model(obj)
        self.run(obj) 
    
    #
    # Hooks
    #

    def new(self):
        self.run()

    def get_model(self, model):
        """This hook must be redefined on child when changing the type of
        the model is a requirement for edit method.
        """
        return model


max_search_results = None

def set_max_search_results(max):
    global max_search_results
    assert max
    max_search_results = max

def get_max_search_results():
    global max_search_results
    return max_search_results
