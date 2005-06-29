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
gui/editors.py:

    Base classes for editors
"""

from stoqlib.gui.dialogs import BasicWrappingDialog
from Kiwi2.Delegates import SlaveDelegate


class BaseEditorSlave(SlaveDelegate):
    """ Base class for editor slaves inheritance. It offers methods for
    setting up focus sequence, required attributes and validated attrs.
    """
    gladefile = None
    widgets = ()

    def __init__(self, conn, model=None):
        # The model attribute represents the main object that has been
        # edited by an interface. It will be always the object the is sent
        # from a kiwi list to an editor.
        self.conn = conn
        self.model = model
        SlaveDelegate.__init__(self, gladefile=self.gladefile,
                               widgets=self.widgets)
        self.setup_proxies()
        self.setup_slaves()

    def setup_proxies(self):
        """ This method should be defined in each child. """

    def setup_slaves(self):
        """ This method should be defined in each child. """



    #
    # Hook methods
    #



    def on_cancel(self):
        """ This is a hook method which must be redefined when some
        action needs to be executed when cancelling in the dialog. """
        return False

    def on_delete_items(self):
        """Redefine this when you need to perform some deletions on database
        table associated with a AdditionListSlave instance."""

    def on_confirm(self):
        """ This is a hook method which must be redefined when some
        action needs to be executed when confirming in the dialog. """
        return self.model

    def validate_confirm(self):
        """ Must be redefined by childs and will perform some validations
        after the click of ok_button. It is interesting to use with some
        special validators that provide some tasks over more than one widget
        value """
        return True


class BaseEditor(BaseEditorSlave):
    """ Base class for editor dialogs. It offers methods of
    BaseEditorSlave, a windows title and OK/Cancel buttons. """

    title = ''
    header = ''
    size = ()

    def __init__(self, conn, model=None):
        BaseEditorSlave.__init__(self, conn, model)
        self.main_dialog = BasicWrappingDialog(self, self.title, 
                                               self.header, self.size)
        self.register_validate_function(self.refresh_ok)

    def refresh_ok(self, validation_value):
        """ Refreshes ok button sensitivity according to widget validators
        status """
        self.main_dialog.ok_button.set_sensitive(validation_value)

class SimpleEntryEditor(BaseEditor):
    """Editor that offers a generic entry to input a string value."""
    gladefile = "SimpleEntryEditor"
    widgets = ('name_entry', 'name_entry_label')
    
    def __init__(self, conn, model, attr_name, name_entry_label='Name:',
                 title=''):
        self.title = title
        self.attr_name = attr_name
        BaseEditor.__init__(self, conn, model)
        self.name_entry_label.set_text(name_entry_label)

    def setup_proxies(self):
        assert self.model
        self.name_entry.set_model_attribute(self.attr_name)
        proxy = self.add_proxy(model=self.model, widgets=['name_entry'])
        
