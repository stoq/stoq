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

from stoq.lib.applist import get_application_names

def main(args):
    apps = get_application_names()
    
    if len(args) >= 2:
        appname = args[1].strip()
        if appname.endswith('/'):
            appname = appname[:-1]

        if not appname in apps:
            raise SystemExit("'%s' is not an application. "
                             "Valid applications are: %s" % (appname, apps))
    else:
        appname = None
    
    from stoq.lib.stoqconfig import AppConfig
    config = AppConfig("stoq")
    if appname:
        config.setup_app(appname, splash=True)
    else:
        appname = config.setup_app(splash=True)

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
