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
database.py:

    Auxiliar methods to work with databases.
"""
from ZODB import POSException 
from Kiwi2 import Delegates 

from stoqlib.gui import dialogs 

def finish_transaction(conn, model=1):
    """ Function to commit/abort created/modified models. """ 
    if model:
        try:
            conn.commit()
            return model
        except POSException.ConflictError, e:
            dialogs._conflict_dialog(e)
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
    if isinstance(model, list) or isinstance(model, tuple):
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
        except POSException.ConflictError, e:
            # In this case it's definitely an RCE
            dialogs._conflict_dialog(e)        
            conn.sync()
            return None
    # Calling a hook for doing something needed after the model insertion in
    # the catalog
    model.after_insert_model(conn)
    return model

