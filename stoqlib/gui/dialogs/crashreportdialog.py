# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Crash report dialog """

import datetime
import platform
import os
import sys
import time
import traceback

import gtk
import kiwi
from kiwi.ui.dialogs import HIGAlertDialog
import psycopg2
import reportlab
import stoqdrivers
import stoqlib

from stoqlib.database.runtime import get_connection
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.webservice import WebService

_ = stoqlib_gettext

def _collect_crash_report(appname, appversion, tracebacks):
    text = ""
    for i, (exctype, value, tb) in enumerate(tracebacks):
        text += '\n'.join(traceback.format_exception(exctype, value, tb))
        if i != len(tracebacks) -1:
            text += '-' * 60

    text += "Report generated at %s %s\n" % (
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        ' '.join(time.tzname))
    text += "System: %r (%s)\n" % (platform.system(),
                                 ' '.join(platform.uname()))
    text += "Distribution: %s\n" % (' '.join(platform.dist()), )
    text += "Architecture: %s\n" % (' '.join(platform.architecture()), )

    text += "Python version: %r (%s)\n" % ('.'.join(map(str, sys.version_info)),
                                         platform.python_implementation())
    text += "PyGTK version: %s\n" % ('.'.join(map(str, gtk.pygtk_version)), )
    text += "GTK version: %s\n" % ('.'.join(map(str, gtk.gtk_version)), )
    text += "Kiwi version: %s\n" % ('.'.join(map(str, kiwi.__version__.version)), )
    text += "Reportlab version: %s\n" % (reportlab.Version, )
    text += "Stoqdrivers version: %s\n" % ('.'.join(map(str, stoqdrivers.__version__)), )
    text += "Stoqlib version: %s\n" % (stoqlib.version, )
    text += "%s version: %s\n" % (appname, appversion)
    text += "Psycopg version: %20s\n" % (psycopg2.__version__, )
    conn = get_connection()
    text += "PostgreSQL version: %20s\n" % (conn.queryOne('SELECT version();'))
    conn.close()

    return text

def show_dialog(appname, appversion, tracebacks):
    d = HIGAlertDialog(parent=None,
                       flags=gtk.DIALOG_MODAL,
                       type=gtk.MESSAGE_WARNING)

    report = _collect_crash_report(appname, appversion, tracebacks)

    d.set_primary(_('We\'r sorry to inform you that an error occurred while '
                    'running %s. Please help us improving Stoq by sending a '
                    'automatically generated report about the incident.\n'
                    'Click on details to see the report text.') % appname, bold=False)
    d.set_details(report)
    d.add_buttons(_('No thanks'), gtk.RESPONSE_NO)
    d.add_buttons(_('Send report'), gtk.RESPONSE_YES)

    if d.run() == gtk.RESPONSE_YES:
        api = WebService()
        response = api.bug_report(report)
        def foo(response, data):
            print data
            gtk.main_quit()
        response.whenDone(foo)
        response.ifError(foo)
        gtk.main()
