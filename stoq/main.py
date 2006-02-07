# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Copyright (C) 2005,2006 Async Open Source
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

import optparse

from stoq.lib.applist import get_application_names

def run_app(options, config, appname):
    from stoq.lib.stoqconfig import AppConfig
    
    appconf = AppConfig()
    appname = appconf.setup_app(appname, splash=True)
    module = __import__("stoq.gui.%s.app" % appname, globals(), locals(), [''])
    if not hasattr(module, "main"):
        raise RuntimeError(
            "Application %s must have a app.main() function")

    module.main(appconf)

    import gtk
    gtk.main()
    appconf.log("Shutting down application")

def main(args):
    parser = optparse.OptionParser()
    parser.add_option('-n', '--hostname',
                      action="store",
                      dest="hostname",
                      help='Database host to connect to')
    parser.add_option('-d', '--database',
                      action="store",
                      dest="database",
                      help='Database name to use')
    parser.add_option('-u', '--username',
                      action="store",
                      dest="username",
                      help='Database username')
    parser.add_option('-c', '--clean',
                      action="store",
                      dest="clean",
                      help='Clean database before running')

    options, args = parser.parse_args(args)

    apps = get_application_names()
    if len(args) < 2:
        appname = None
    else:
        appname = args[1].strip()
        if appname.endswith('/'):
            appname = appname[:-1]

        if not appname in apps:
            raise SystemExit("'%s' is not an application. "
                                 "Valid applications are: %s" % (appname, apps))

    from stoqlib.lib.runtime import (register_configparser_settings,
                                     register_application_names)
    register_configparser_settings('stoq', 'stoq.conf')
    register_application_names(apps)

    from stoqlib.lib.configparser import config
    if options.hostname:
        config.set_database(options.hostname)
    if options.database:
        config.set_database(options.database)
    if options.username:
        config.set_database(options.username)

    run_app(options, config, appname)
