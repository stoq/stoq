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
interface/services.py:

    Base classes and functions to run applications
"""

import traceback
import warnings
import sys 


import gtk
import gobject
from IndexedCatalog.Shelf import Shelf
from ZODB.POSException import ConflictError
from Kiwi2.initgtk import quit_if_last
from Kiwi2.Delegates import Delegate
from Kiwi2.Views import SlaveView, BaseView


#
# Exceptions/warnings
#

class StoqlibWarning(Warning):
    pass

def _warn(msg):
    warnings.warn('\n%s\n' % msg, StoqlibWarning)

class ModelDataError(Exception): pass

#
# Expects an main window class, which takes one argument: the app (for
# shutdown purposes)
#

class BaseApp:
    """ Base class for application control. """
    def __init__(self, main_window_class, sync_time=10000):
        # The self should be passed to main_window to let it access
        # shutdown and do_sync methods.
        self.main_window = main_window_class(self)
        gobject.timeout_add(sync_time, self.do_sync)

    def run(self):
        self.main_window.show()

    def shutdown(self, *args):
        quit_if_last()

    def do_sync(self, *args):
        if hasattr(self.main_window, 'sync'):
            self.main_window.sync()
        return True

#
# Expects an app, with app.shutdown available as a handler
#

class BaseAppWindow(Delegate):
    """ Class to be inherited by applications main window.  """
    gladefile = toplevel_name = ''
    widgets = ()
    def __init__(self, app, keyactions=None):
        Delegate.__init__(self, delete_handler=app.shutdown,
                          keyactions=keyactions, widgets=self.widgets,
                          gladefile=self.gladefile,
                          toplevel_name=self.toplevel_name)

    def set_sensitive(self, widgets, value):
        """Sets one or more widgets to state sensitive. XXX: Kiwi?"""
        for widget in widgets:
            widget.set_sensitive(value)

    def get_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for getting dialogs. """
        return get_dialog(self, dialog_class, *args, **kwargs)

    def run_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for running dialogs. """
        return run_dialog(dialog_class, self, *args, **kwargs)

    def lookup_model(self, conn, model):
        """ Encapsuled method for looking up models. """
        return lookup_model(conn, model)

    def ensure_insert_model(self, conn, model):
        """ Encapsuled method for inserting models in catalogs. """
        return ensure_insert_model(conn, model)

    def finish_transaction(self, conn, model=1, keep=0):
        """ Encapsuled method for committing/aborting changes in models.
        This method is special (and different from the standalone
        finish_transaction) because, unless keep=1 is provided, the
        connection provided is also closed."""
        # Default model is 1 which means that we'll commit if nothing
        # was passed in.
        if not isinstance(conn, Shelf):
            raise TypeError, "conn must be Shelf, got %r" % conn
        ret = finish_transaction(conn, model)
        if not keep:
            conn.close()
        return ret


#
# Service functions
#


def get_dialog(parent, dialog_class, *args, **kwargs):
    """ Returns a dialog.
    - parent: the window which is opening the dialog;
    - dialog_class: the dialog class;
    - *args, **kwargs: the arguments which should be used on dialog_class
      instantiation;
    """
    d = dialog_class(*args, **kwargs)

    if isinstance(parent, BaseView):     
        parent = parent.toplevel.get_toplevel()
        if parent:
            d.set_transient_for(parent)
    return d

def run_dialog(dialog_class, parent, *args, **kwargs):
    dialog = get_dialog(parent, dialog_class, *args, **kwargs)
    if hasattr(dialog, 'main_dialog'):
        dialog = dialog.main_dialog

    dialog.toplevel.run()
    retval = dialog.retval
    dialog.destroy()
    return retval

def finish_transaction(conn, model=1):
    """ Function to commit/abort created/modified models. """ 
    if model:
        try:
            conn.commit()
            return model
        except ConflictError, e:
            _conflict_dialog(e)
            conn.sync()
            return None
    else:
        conn.abort()
        conn.sync()
        return None

def lookup_model(conn, model):
    """ Function to lookup the model according to the connection which
    should be used by a dialog.
    - model: can be a model, or a list of models. """
    if isinstance(model, (list, tuple)):
        model = [conn.lookup(item) for item in model]
    else:
        model = conn.lookup(model)
    return model

def ensure_insert_model(conn, model):
    if not model:
        raise AttributeError, "Trying to insert a None model in the catalog."
    cat = conn.get_catalog(model.__class__)
    if not cat.has_object(model):
        try:
            cat.insert(model)
        except ConflictError, e:
            # In this case it's definitely an RCE
            _conflict_dialog(e)        
            conn.sync()
            return None
    # Calling a hook for doing something needed after the model insertion in
    # the catalog
    model.after_insert_model(conn)
    return model

def _conflict_dialog(e):
    from stoqlib.interface.dialogs import notify_dialog
    traceback.print_stack()
    sys.stderr.write("XXX ConflictError: %s" % str(e))
    msg = ("A conflict was generated at the end of the transaction. \n "
           "Please cancel and do the transaction again.\n\n"
           "(This problem was registered and will be evaluated.)")
    notify_dialog(msg)

def notify_if_raises(win, check_func, exceptions=ModelDataError, 
                     text="An error ocurred: %s"):
    from stoqlib.interface.dialogs import notify_dialog
    try:
        check_func()
    except exceptions, e:
        notify_dialog(text % e)
        return True 
    return False
        
