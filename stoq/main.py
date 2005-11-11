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
##              Johan Dahlin                <jdahlin@async.com.br>
##
"""
stoq/main.py:

        Routines to start Stoq applications
"""

import glob
import os


def _check_class_module(object, app_module):
    return object.__module__ == app_module.__name__

def _get_apps_data():
    import stoq
    applications = []
    expr = os.path.join(os.path.split(stoq.__file__)[0],
                        'gui', '*', 'app.py')
    for sub_dir in glob.glob(expr):
        # sub_dir is stoq/gui/foobar/app.py
        # dirname is stoq/gui/foobar
        # appname is foobar
        
        dirname = os.path.split(sub_dir)[0]
        appname = os.path.split(dirname)[1]
        module = __import__("stoq.gui.%s.%s" % (appname, appname),
                            globals(), locals(), appname)
        applications.append((appname, module))
    return applications

def get_app_full_names():
    # Import these modules here to reduce the startup time
    import inspect
    from stoq.gui.application import AppWindow

    applications = _get_apps_data()
    app_full_names = []
    for app_name, module in applications:
        for name, member in inspect.getmembers(module, inspect.isclass):
            if not _check_class_module(member, module):
                continue
            if not issubclass(member, AppWindow):
                continue
            app_full_name = getattr(member, 'app_name', None)
            if not app_full_name:
                raise ValueError('App %s must have an app_name attribute'
                                 % member)
            app_full_names.append((app_name, app_full_name))
    return app_full_names

def get_app_list():
    """Collects the application names from the gui/ directory and
    sets a list member
    """
    applications = _get_apps_data()
    app_names = [name for name, module in applications]
    app_names.sort()
    return app_names

def main(args):
    apps = get_app_list()
    
    if len(args) < 2:
       raise SystemExit("Usage: stoq <application>. "
                        "Valid applications are: %s""" % apps)

    appname = args[1].strip()
    if appname.endswith('/'):
        appname = appname[:-1]

    if not appname in apps:
        raise SystemExit("'%s' is not an application. "
                         "Valid applications are: %s" % (appname, apps))
    
    from stoq.lib.stoqconfig import AppConfig
    config = AppConfig("stoq")
    config.setup_app(appname, splash=True)

    module = __import__("stoq.gui.%s.app" % appname,
                        globals(), locals(), appname)
    if not hasattr(module, "main"):
        raise RuntimeError(
            "Application %s must have a app.main() function")

    if not 'noexec' in args:
        module.main(config)

    import gtk
    gtk.main()
    config.log("Shutting down application")
