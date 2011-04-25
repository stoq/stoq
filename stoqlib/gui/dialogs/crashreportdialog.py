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
import json
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
from stoqlib.gui.base.dialogs import get_current_toplevel
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.webservice import WebService

_ = stoqlib_gettext

def _collect_crash_report(params, tracebacks):
    text = ""
    text += "Report generated at %s %s\n" % (
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        ' '.join(time.tzname))
    text += ('-' * 80) + '\n'

    for i, (exctype, value, tb) in enumerate(tracebacks):
        text += '\n'.join(traceback.format_exception(exctype, value, tb))
        if i != len(tracebacks) -1:
            text += '-' * 60
    text += ('-' * 80) + '\n'

    text += 'Content of %s:\n' % (params['log-filename'], )
    text += open(params['log-filename']).read()
    text += ('-' * 80) + '\n'

    uptime = params['app-uptime']
    text += "Application uptime: %dh%dmin\n" % (uptime / 3600,
                                                (uptime % 3600) / 60)
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
    text += "%s version: %s\n" % (params['app-name'], params['app-version'])
    text += "Psycopg version: %20s\n" % (psycopg2.__version__, )
    conn = get_connection()
    text += "PostgreSQL version: %20s\n" % (conn.queryOne('SELECT version();'))
    conn.close()
    text += ('-' * 80) + '\n'
    return text

def show_dialog(params, tracebacks):
    parent = get_current_toplevel()
    d = HIGAlertDialog(parent=parent,
                       flags=gtk.DIALOG_MODAL,
                       type=gtk.MESSAGE_WARNING)
    report = _collect_crash_report(params, tracebacks)

    d.set_primary(_('We\'r sorry to inform you that an error occurred while '
                    'running %s. Please help us improving Stoq by sending a '
                    'automatically generated report about the incident.\n'
                    'Click on details to see the report text.') % (
            params['app-name'], ), bold=False)

    sw = gtk.ScrolledWindow()
    view = gtk.TextView()
    view.set_size_request(500, 350)
    view.get_buffer().set_text(report)
    sw.add(view)
    view.show()
    d.set_details_widget(sw)
    no_button = d.add_button(_('No thanks'), gtk.RESPONSE_NO)
    yes_button = d.add_button(_('Send report'), gtk.RESPONSE_YES)

    response = d.run()
    if response == gtk.RESPONSE_NO:
        return

    no_button.hide()
    yes_button.set_sensitive(False)
    parent.destroy()
    api = WebService()
    response = api.bug_report(report)

    if platform.system() != 'Windows':
        yes_button.set_label(_('Sending...'))
        def callback(response, data):
            r = json.loads(data)
            label = gtk.LinkButton(
                r['report-url'],
                _("Report %s successfully opened") % r['report'])
            d.vbox.pack_start(label)
            label.show()
            yes_button.set_label(_("Close"))
            yes_button.set_sensitive(True)
        response.whenDone(callback)
        response.ifError(callback)
        d.run()
    raise SystemExit
