# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Copyright (C) 2005 Async Open Source
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
# USA.
#

import gettext
import os

from kiwi.environ import environ
from stoqlib.environ import get_pixmaps_dir as get_stoqlib_pixmaps

from stoq.lib.environ import (get_base_dir, get_locale_dir, get_glade_dir,
                              get_pixmaps_dir)

appdir = os.path.join(get_base_dir(), "stoq", "gui")

# Tell gettext that translations (.mo files) for the translation
# domain stoq can be found in locale_dir, 
gettext.bindtextdomain('stoq', get_locale_dir())

# We always want to load in utf-8 charset, makes everything
# a lot easier when using pygtk
gettext.bind_textdomain_codeset('stoq', 'utf-8')

# Set the default domain to stoq, so we don't need to explicitly
# specify the domain each time we want to do a translation lookup 
gettext.textdomain('stoq')

def get_app_list():
    # Collects the application names from the gui/ directory and
    # sets a list member. 

    # Find out what applications we have available
    applications = []
    for sub_dir in os.listdir(appdir):
        dir = os.path.join(appdir, sub_dir)
        if os.path.isfile(os.path.join(dir, 'app.py')):
            applications.append(sub_dir)
    applications.sort()
    return applications

# A list of subdirectories in stoq/gui/
glade_dirs = ['editors', 'components', 'search', 'slaves', 'templates', 
              'wizards'] + get_app_list()

for dir in glade_dirs:
    path = os.path.join(get_base_dir(), "stoq", "gui", dir, "glade")
    if os.path.exists(path) and os.path.isdir(path):
        environ.add_resource("glade", path)

glade_dir = get_glade_dir()
if os.path.exists(glade_dir) and os.path.isdir(glade_dir):
    environ.add_resource("glade", glade_dir)

environ.add_resource("pixmap", get_pixmaps_dir())
environ.add_resource("pixmap", get_stoqlib_pixmaps())

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
