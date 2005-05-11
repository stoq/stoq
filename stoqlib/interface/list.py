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
interface/list.py:

    List management for common dialogs.
"""

import gtk
from Kiwi2 import Delegates
from stoqlib.interface import dialogs, search, editors, services

class AdditionListSlave(Delegates.SlaveDelegate):
    """ A slave that offers a simple list and its management. 
    
    editor_class    = represents the window that is going to be open when user 
                      clicks on add_button or edit_button.
    columns         = columns definition for AdditionListSlave klist widget.
    klist_objects   = list of inicial objects to sendo to AdditionListSlave
                      klist widget.
    editor_kwargs   = additional arguments for editor class constructor.

    on_delete_items = a hook method that must be defined in parent instance
                      to perform some tasks in database during deletions.
    """

    # I keep this in a class attribute to avoid the methods calling
    # 'get_selected()' many times.
    # This will be set in _on_klist_selected()
    objs_selected = None
    toplevel_name = gladefile = 'AdditionListSlave'
    widgets = ('add_button', 'delete_button', 'klist', 'edit_button')

    def __init__(self, parent, editor_class, columns, klist_objects=None,
                 **editor_kwargs):
        Delegates.SlaveDelegate.__init__(self, toplevel_name=self.toplevel_name,
                               gladefile=self.gladefile, widgets=self.widgets)
        self.editor_class = editor_class
        self.columns = columns
        self.editor_kwargs = editor_kwargs
        
        self.parent = parent
        self._setup_list()

        if klist_objects:
            self.klist.add_list(klist_objects)
            
        self.update_widgets()

    def _setup_list(self):
        self.klist.set_column_definitions(self.columns)
        self.klist.set_selection_mode(gtk.SELECTION_EXTENDED)

    def update_widgets(self, *args):
        widgets = (self.add_button, self.delete_button, self.edit_button)
        for w in widgets:
            w.set_sensitive(True)

        if not self.klist.get_selected():
            self.delete_button.set_sensitive(False)
            self.edit_button.set_sensitive(False)
        elif len(self.klist.get_selected()) > 1:
            self.edit_button.set_sensitive(False)

    def run(self, model=None):
        edit_mode = model
        model = services.run_dialog(self.editor_class, conn=self.parent.conn, 
                           model=model, **self.editor_kwargs)
        if not services.finish_transaction(self.parent.conn, model):
            services._warn('Transaction not concluded. Probably a failure.')
            return
        if edit_mode:
            self.klist.update_instance(model)
            self.parent.on_edit_item(model)
        else:
            self.klist.add_instance(model)
            self.parent.on_add_item(model)

        # As we have a selection extended mode for kiwi list, we 
        # need to unselect everything before select the new instance.
        self.klist.unselect_all()
        self.klist.select_instance(model)
        self.update_widgets()

    def edit(self):
        assert len(self.objs_selected) == 1, ("Bug: You should have just one "
                                              "item selected, found %s" 
                                              % len(self.objs_selected))
        model = self.objs_selected[0]
        self.run(model)

    #
    # Public API
    #

    def hide_add_button(self):
        self.add_button.hide()

    def hide_edit_button(self):
        self.edit_button.hide()

    def hide_del_button(self):
        self.del_button.hide()

    #
    # Kiwi handlers
    #

    def on_klist__double_click(self, *args):
        self.edit()

    def on_klist__selection_change(self, *args):
        self.objs_selected = self.klist.get_selected()
        self.update_widgets()

    def on_add_button__clicked(self, *args):
        self.run()
    
    def on_edit_button__clicked(self, *args):
        self.edit()

    def on_delete_button__clicked(self, *args):
        assert self.objs_selected, 'Bug: there is no objects selected.'
        qty = len(self.objs_selected)
        if qty > 1:
            msg = _('Are you sure you want delete these items ?')
        else:
            msg = _('Are you sure you want delete this item ?')

        if not dialogs.confirm_dialog(msg):
            return

        self.parent.on_delete_items(self.objs_selected)

        if qty == len(self.klist):
            self.klist.clear()

        else:
            for instance in self.objs_selected:
                self.klist.remove_instance(instance)
        
        self.klist.unselect_all()
        self.update_widgets()

class AdditionListDialog(dialogs._BasicPluggableDialog):
    size = (500, 500)

    def __init__(self, parent, editor_class, columns, klist_objects,
                 title='', **editor_kwargs):
        self.title = title
        dialogs._BasicPluggableDialog.__init__(self)
        self.conn = parent.conn
        self._initialize(editor_class, columns, klist_objects, **editor_kwargs)

    def _initialize(self, editor_class, columns, klist_objects,
                    **editor_kwargs):
        self.addition_list = AdditionListSlave(self, editor_class, columns,
                                               klist_objects, **editor_kwargs)

        self.addition_list.on_confirm = self.on_confirm
        self.addition_list.on_cancel = self.on_cancel
        self.addition_list.validate_confirm = self.validate_confirm

        dialogs._BasicPluggableDialog._initialize(self, self.addition_list,
                                                  size=self.size,
                                                  title=self.title)

    #
    # _BasicPluggableDialog callbacks
    #

    def on_cancel(self):
        return None

    def on_confirm(self):
        return [item for item in self.addition_list.klist]

    def validate_confirm(self):
        return True    

    #
    # AdditionListSlave callbacks
    #

    def on_add_item(self, obj):
        pass

    def on_delete_items(self, *objs):
        pass

    def on_edit_item(self, obj):
        pass

class SimpleListDialog(dialogs._BasicDialog):
    size = (500, 400)

    def __init__(self, columns, objects, parent=None, hide_cancel_btn=True):
        dialogs._BasicDialog.__init__(self)
        dialogs._BasicDialog._initialize(self, size=self.size)

        if hide_cancel_btn:
            self.cancel_button.hide()

        self.setup_slave(columns, objects, parent)

    def setup_slave(self, columns, objects, parent):
        self.list_slave = search._BaseListSlave(parent, columns, objects)
        self.list_slave.klist.set_selection_mode(gtk.SELECTION_EXTENDED)
        self.attach_slave('main', self.list_slave)

    # _BasicDialog 'confirm' method override
    def confirm(self):
        self.retval = self.list_slave.klist.get_selected()
        self.close()

