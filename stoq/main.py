# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Stoq startup routines"""


import sys
import gettext

from stoq.lib.applist import get_application_names
from stoq.lib.configparser import StoqConfig
from stoq.lib.startup import setup, get_option_parser

_ = gettext.gettext

def _run_first_time_wizard(config):
    from stoqlib.gui.base.dialogs import run_dialog
    from stoq.gui.config import FirstTimeConfigWizard
    model = run_dialog(FirstTimeConfigWizard, None)
    if not model:
        raise SystemExit("No configuration data provided")
    return model.db_settings

def _initialize(options):
    from kiwi.ui.dialogs import error
    config = StoqConfig()

    if not config.has_installed_config_data():
        config.install_default(_run_first_time_wizard(config))
        options.clean = True

    try:
        config.load_config()
        config.check_connection()
    except:
        raise
        type, value, trace = sys.exc_info()
        error(_('Could not open database config file'),
              long=_("Invalid config file settings, got error '%s', "
                     "of type '%s'" % (value, type)))
        raise SystemExit("Error: bad config file")

    # XXX: progress dialog for connecting (if it takes more than
    # 2 seconds) or creating the database
    try:
        setup(config, options)
    except Exception, e:
        raise
        error(_('Could not connect to database'), long=str(e))
        raise SystemExit("Error: bad connection settings provided")

def _run_app(options, appname):
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
    parser = get_option_parser()
    parser.add_option('', '--clean',
                      action="store_true",
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

    _initialize(options)
    _run_app(options, appname)
