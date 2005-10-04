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

try:
    # We can't use from .. import ... as module until pyflakes
    # can handle it fixed
    from stoq import __installed__
    module = __installed__
except ImportError:
    try:
        from stoq import __uninstalled__
        module = __uninstalled__
    except ImportError:
        raise SystemExit("FATAL ERROR: Internal error, could not load"
                         "stoq.\n"
                         "Tried to start stoq but critical configuration "
                         "were are missing.\n")

# A list of subdirectories in stoq/gui/
for dir in ['editors', 'components', 'pos', 'search',
            'slaves', 'templates', 'till', 'wizards']:
    path = os.path.join(module.basedir, "stoq", "gui", dir, "glade")
    if os.path.exists(path) and os.path.isdir(path):
        environ.add_resource("glade", path)

if os.path.exists(module.glade_dir) and os.path.isdir(module.glade_dir):
    environ.add_resource("glade", module.glade_dir)

environ.add_resource("pixmap", module.pixmap_dir)

appdir = os.path.join(module.basedir, "stoq", "gui")

# Tell gettext that translations (.mo files) for the translation
# domain stoq can be found in locale_dir, 
gettext.bindtextdomain('stoq', module.locale_dir)

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
