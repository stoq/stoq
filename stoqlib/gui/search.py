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
"""
gui/search.py:

    Implementation of basic dialogs for search
"""

import gtk
from Kiwi2 import Delegates 

from stoqlib.gui import dialogs
from stoqlib import database



#
# Slaves for search dialogs.
#



class BaseListSlave(Delegates.SlaveDelegate):
    """ Base slave for dialogs that need a Kiwi List. If the 'parent' class
    send a 'parent' argument, the method update_widgets will be called when 
    the list be selected ou double clicked. """

    gladefile = 'BaseListSlave'
    widgets = ('klist', )

    def __init__(self, parent=None, columns=None, objects=None):
        Delegates.SlaveDelegate.__init__(self, widgets=self.widgets, 
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


class SearchSlave(Delegates.SlaveDelegate):
    """ Slave for internal use of SearchDialog, offering an eventbox for
    insertion by an user search bar and managing the "Filter" and "Clear" 
    buttons. """

    gladefile = 'SearchSlave'
    widgets = ('search_button', 'erase_button', 'searchbar_holder')

    def __init__(self, parent):
        Delegates.SlaveDelegate.__init__(self, gladefile=self.gladefile,
                                         widgets=self.widgets)
        self.parent = parent



    #
    # Kiwi handlers
    #



    def on_search_button__clicked(self, *args):
        self.parent.update_klist()

    def on_erase_button__clicked(self, *args):
        self.parent.clear_klist()
        self.parent.clear_fields()


class SearchEditorToolBar(Delegates.SlaveDelegate):
    """ Slave for internal use of SearchEditor, offering an eventbox for a
    toolbar and managing the 'New' and 'Edit' buttons. """

    toplevel_name = 'ToolBar'
    gladefile = 'SearchEditor'
    widgets = ('new_button', 'edit_button', 'toolbar_holder')

    def __init__(self, parent):
        Delegates.SlaveDelegate.__init__(self, toplevel_name=self.toplevel_name,
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



class SearchDialog(dialogs.BasicDialog):
    """ Base class for *all* the search dialogs, responsible for the list
    construction and "Filter" and "Clear" buttons management.

    This class must be subclassed and its subclass *must* implement the 
    methods 'get_columns' and 'get_query' (if desired, 'get_query' can be 
    implemented in the user's slave class, so SearchDialog will get its 
    slave instance and call 'get_query' directly). Its subclass also must 
    implement a setup_slaves method and call its equivalent base class 
    method as in:

    def setup_slave(self):
        SearchDialog.setup_slaves(self)

    or then, call it in its constructor, like:

    def __init__(self, *args):
        SearchDialog.__init__(self)
        ...
    """
    main_label_text = ''
    title = ''
    size = ()
            
    def __init__(self, table, hide_footer=True):
        dialogs.BasicDialog.__init__(self)
        dialogs.BasicDialog._initialize(self, hide_footer=hide_footer,
                                        main_label_text=self.main_label_text, 
                                        title=self.title, size=self.size)
        self.table = table
        self.conn = database.get_model_connection()
        assert self.conn
        self.setup_slaves()
        self.update_edit_button()

    def setup_slaves(self, **kwargs):
        self.klist_slave = BaseListSlave(parent=self)
        self.klist = self.klist_slave.klist

        self.search_bar = SearchSlave(self)

        self.attach_slave('main', self.klist_slave)
        self.attach_slave('header', self.search_bar)

    def update_klist(self, *args):
        self.klist.clear()

        query = self.get_query()
        objs = self.table.select(query, connection=self.conn)
        if objs.count():
            self.klist.add_list(objs)

        # A hack to allow me set the sensitive state of edit_button for
        # SearchEditor. Also, internal operations must be done in
        # update_edit_button; update_widgets is *exclusive* for SearchEditor
        # and SearchDialog subclasses now.
        self.update_edit_button()
        self.update_widgets()

    def clear_klist(self):
        self.klist.clear()
        self.update_widgets()
        self.update_edit_button()

    def confirm(self):
        self.retval = self.klist.get_selected()
        self.close()

    def update_edit_button(self):
        pass



    #
    # Hook methods
    #



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

    def get_query(self):
        user_slave = self.search_bar.get_slave('searchbar_holder')
        return user_slave.get_query()


class SearchEditor(SearchDialog):
    """ Base class for a search "editor" dialog, that offers a 'new' and 
    'edit' button on the dialog footer. The 'new' and 'edit' buttons will 
    call 'editor_class' sending as its parameters a new connection and the 
    object to edit for 'edit' button.
    
    This is also a subclass of SearchDialog and the same rules are required. 
    """

    def __init__(self, table, editor_class, hide_footer=True):
        SearchDialog.__init__(self, table, hide_footer)
        self.editor_class = editor_class
        self.klist.connect('double_click', self.edit)

    def setup_slaves(self):
        SearchDialog.setup_slaves(self)
        self.toolbar = SearchEditorToolBar(self)
        self.attach_slave('extra_holder', self.toolbar)

    def update_edit_button(self):
        self.toolbar.edit_button.set_sensitive(len(self.klist))

    def run(self, obj=None):
        if obj: 
            obj = self.table.get(id=obj.id, connection=self.conn)
        
        rv = dialogs.run_dialog(self.editor_class, self, 
                                self.conn, obj)
        if not rv:
            self.conn.rollback()
            self.conn.begin()
            return
        self.conn.commit()
        self.update_klist()
        self.klist.select_instance(rv)

    def edit(self, widget, obj=None):
        if obj is None:
            obj = self.klist.get_selected()[0]
        self.run(obj) 
    

    
    #
    # Hook methods
    #



    def clear_fields(self):
        """ This hook is used when an Erase button was pushed to clean 
        fields defined by the constructor """
        
    def new(self):
        self.run()
