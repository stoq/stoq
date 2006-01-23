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
"""
stoq/lib/applist.py:

    Listing and importing applications
"""

import glob
import os

import stoq

def get_application_names():
    """Get a list of application names, useful for launcher programs
    
    @returns: application names
    """
    applications = []
    expr = os.path.join(os.path.split(stoq.__file__)[0],
                        'gui', '*', 'app.py')
    for sub_dir in glob.glob(expr):
        # sub_dir is stoq/gui/foobar/app.py
        # dirname is stoq/gui/foobar
        # appname is foobar
        
        dirname = os.path.split(sub_dir)[0]
        appname = os.path.split(dirname)[1]
        applications.append(appname)
    return applications

def get_app_descriptions():
    """@returns: a list of tuples with some important Stoq application
    informations. Each tuple has the following data: 
        * Application name
        * Application full name
        * Application icon name
    """
    # Import these modules here to reduce the startup time
    import inspect
    from stoq.gui.application import AppWindow

    applications = get_application_names()
    app_desc = []
    for appname in applications:
        module = __import__("stoq.gui.%s.%s" % (appname, appname),
                            globals(), locals(), appname)
        for name, member in inspect.getmembers(module, inspect.isclass):
            if member.__module__ != module.__name__:
                continue
            if not issubclass(member, AppWindow):
                continue
            app_full_name = getattr(member, 'app_name', None)
            app_icon_name = getattr(member, 'app_icon_name', None)
            if not app_full_name:
                raise ValueError('App %s must have an app_name attribute'
                                 % member)
            app_desc.append((appname, app_full_name, app_icon_name))
    return app_desc
