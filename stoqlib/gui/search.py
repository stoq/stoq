# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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

import gtk
import gobject
from twisted.python.components import Adapter
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.widgets.list import Column
from sqlobject.sresults import SelectResults
from sqlobject.sqlbuilder import LIKE, AND, func, OR
from sqlobject.col import (SOStringCol, SOFloatCol, SOIntCol,
                           SODateTimeCol)

import stoqlib
from stoqlib.gui.dialogs import BasicDialog, run_dialog
from stoqlib.exceptions import _warn
from stoqlib.common import is_integer, is_float
from stoqlib.database import get_model_connection
from stoqlib.gui.columns import FacetColumn, ForeignKeyColumn


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
            raise Exception, ("You must supply columns via parameter of in"
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

    def on_klist__selection_change(self, *args):
        self.update_widgets()

    def on_klist__double_click(self, *args):
        self.update_widgets()


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
    gladefile = 'SearchBar'
    
    widgets = ('search_button',
               "search_entry",
               "search_icon")

    SEARCH_ICON_SIZE = gtk.ICON_SIZE_LARGE_TOOLBAR
    ANIMATE_TIMEOUT = 200

    def __init__(self, parent, table_type, columns=None, query_args=None,
                 search_callback=None):
        SlaveDelegate.__init__(self, gladefile=self.gladefile, 
                               widgets=self.widgets)
        self._animate_search_icon_id = -1
        self.search_icon.set_from_stock("searchtool-icon1", 
                                        self.SEARCH_ICON_SIZE)
        self._update_widgets()
        self.parent = parent
        self.conn = self.parent.conn
        self.columns = columns
        self.table_type = table_type
        self.query_args = query_args
        self._search_callback = search_callback
        self._split_field_types()

    def _update_widgets(self):
        if self.search_entry.get_text() != '':
            self.search_button.set_sensitive(True)
        else:
            self.search_button.set_sensitive(False)
        self.search_entry.grab_focus()

    def get_search_string(self):
        return self.search_entry.get_text()

    def set_search_string(self, search_str):
        return self.search_entry.set_text(search_str)


    #
    # Preparing query fields and groups
    #



    def _split_field_types(self):
        self.int_fields = []
        self.float_fields = []
        self.str_fields = []
        # TODO Just a beginnig for a date time suport. We will implement 
        # this part soon and when we add a slave area for DateTime widgets.
        self.dtime_fields = []
        if not self.columns:
            return

        attributes = [c.attribute for c in self.columns]
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

            for column in table_type.sqlmeta._columns:
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
                elif (isinstance(column, SODateTimeCol)
                      and value not in self.dtime_fields):
                     self.dtime_fields.append(value)

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



    #
    # Building query
    #



    def _build_query(self, search_str):
        """Here we build queries after check the search string type. 
        Queries are always optimized for field types to avoid database 
        input syntax errors and also make smart searches."""
        query = []
        if is_integer(search_str):
            self._set_query_int(search_str, query)
        elif is_float(search_str):
            self._set_query_float(search_str, query)
        else:
            # Instead of checking for another type, perform later a 
            # query for string fields and for any search string.
            pass
        self._set_query_str(search_str, query)

        query = OR(*query)
        return query



    #
    # Performing search
    #



    def _run_query(self):
        search_str = self.get_search_string()
        if not search_str:
            # Clear the kiwi list if we don't have a valid search string
            self.parent.update_klist()
            return
        query = self._build_query(search_str)

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
        
        objs = self.table_type.select(query, **kwargs)
        objs = self.parent.filter_results(objs)
        self.parent.update_klist(objs)

    def search_items(self):
        self.start_animate_search_icon()
        if self._search_callback:
            # Perform an alternative search as desired
            self._search_callback()
        else:
            self._run_query()
        self.stop_animate_search_icon()



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
        self._animate_search_icon_id = \
            gobject.timeout_add(self.ANIMATE_TIMEOUT, 
                                self._animate_search_icon().next)
    
    def stop_animate_search_icon(self):
        if self._animate_search_icon_id == -1:
            # TODO: it's wierd that _warn method is private. Need some refactoring
            _warn("Search icon animation hasn't started")
        gobject.source_remove(self._animate_search_icon_id)
    

    
    #
    # Callbacks
    # 
    


    def on_search_button__clicked(self, *args):
        self.search_items()

    def on_search_entry__activate(self, *args):
        self.search_items()

    def on_search_entry__changed(self, *args):
        self._update_widgets()


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
        ...
    """
    main_label_text = ''
    title = ''
    size = ()
            
    def __init__(self, table, search_table=None,
                 hide_footer=True, title='', 
                 selection_mode=gtk.SELECTION_BROWSE):
        BasicDialog.__init__(self)
        title = title or self.title
        avaliable_modes = [gtk.SELECTION_BROWSE, gtk.SELECTION_MULTIPLE]
        if selection_mode not in avaliable_modes:
            raise ValueError('Invalid selection mode %' % selection_mode)
        self.selection_mode = selection_mode
        BasicDialog._initialize(self, hide_footer=hide_footer,
                                main_label_text=self.main_label_text, 
                                title=title, size=self.size)
        self.set_ok_label(_('Select Items'))
        self.table = table
        self.search_table = search_table or self.table
        self.conn = get_model_connection()
        assert self.conn
        self.setup_slaves()

    def setup_slaves(self, **kwargs):
        self.klist_slave = BaseListSlave(parent=self)
        self.attach_slave('main', self.klist_slave)
        self.klist = self.klist_slave.klist
        # We can not change this through gazpacho because BaseListSlave 
        # can be used for some other classes which should always redefine
        # this mode
        self.klist.set_selection_mode(self.selection_mode)

        columns = self.get_columns()
        query_args = self.get_query_args()
        self.search_bar = SearchBar(self, self.search_table, columns, 
                                    query_args=query_args)
        self.attach_slave('header', self.search_bar)


    def clear_klist(self):
        self.klist.clear()
        self.update_widgets()

    def confirm(self):
        mode = self.klist.get_selection_mode()
        if mode == gtk.SELECTION_BROWSE:
            self.retval = self.klist.get_selected()
        else:
            self.retval = self.klist.get_selected_rows()
        self.close()

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
            self.klist.select_instance(objs[0])
        self.update_widgets()

    def on_delete_items(self, items):
        """ This hook could be useful for AdditionListSlave instances. It 
        must be redefined by childs when it's necessary. """

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
                 search_table=None, hide_footer=True, title='',
                 selection_mode=gtk.SELECTION_BROWSE):
        SearchDialog.__init__(self, table, search_table,
                              hide_footer=hide_footer, title=title,
                              selection_mode=selection_mode)
        self.interface = interface
        self.editor_class = editor_class
        self.klist.connect('double_click', self.edit)
        self.update_widgets()

    def setup_slaves(self):
        SearchDialog.setup_slaves(self)
        self.toolbar = SearchEditorToolBar(self)
        self.attach_slave('extra_holder', self.toolbar)

    def update_widgets(self, *args):
        self.toolbar.edit_button.set_sensitive(len(self.klist))

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
        
        rv = run_dialog(self.editor_class, self, self.conn, obj)
        if not rv:
            self.conn.rollback()
            self.conn.begin()
            return

        self.conn.commit()
        self.search_bar.search_items()

        if rv in self.klist:
            self.klist.select_instance(rv)


    def edit(self, widget, obj=None):
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
    

    
    #
    # Hooks
    #



    def new(self):
        self.run()
