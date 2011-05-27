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
import sys
import time
import traceback

import gtk
import kiwi
from kiwi.log import Logger
from kiwi.ui.dialogs import HIGAlertDialog
import psycopg2
import reportlab
import stoqdrivers
import stoqlib

from stoqlib.database.runtime import get_connection
from stoqlib.exceptions import StoqlibError
from stoqlib.gui.base.dialogs import get_current_toplevel
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.webservice import WebService

_ = stoqlib_gettext
log = Logger('stoqlib.crashreporter')

_N_TRIES = 3


class CrashReportDialog(object):
    def __init__(self, parent, params, tracebacks):
        self._parent = parent
        self._params = params
        self._tracebacks = tracebacks
        self._count = 0
        self._api = WebService()
        self._report = self._collect()
        self._show_dialog()

    def _show_dialog(self):
        self._dialog = HIGAlertDialog(parent=self._parent,
                                      flags=gtk.DIALOG_MODAL,
                                      type=gtk.MESSAGE_WARNING)

        self._dialog.set_primary(
            _('We\'r sorry to inform you that an error occurred while '
              'running %s. Please help us improving Stoq by sending a '
              'automatically generated report about the incident.\n'
              'Click on details to see the report text.') % (
            self._params['app-name'], ), bold=False)

        sw = gtk.ScrolledWindow()
        view = gtk.TextView()
        view.set_size_request(500, 350)
        view.get_buffer().set_text(self._report)
        sw.add(view)
        view.show()
        self._dialog.set_details_widget(sw)
        self._no_button = self._dialog.add_button(_('No thanks'),
                                                  gtk.RESPONSE_NO)
        self._yes_button = self._dialog.add_button(_('Send report'),
                                                   gtk.RESPONSE_YES)

    def _collect(self):
        text = ""
        text += "Report generated at %s %s\n" % (
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            ' '.join(time.tzname))
        text += ('-' * 80) + '\n'

        for i, (exctype, value, tb) in enumerate(self._tracebacks):
            text += '\n'.join(traceback.format_exception(exctype, value, tb))
            if i != len(self._tracebacks) -1:
                text += '-' * 60
        text += ('-' * 80) + '\n'

        text += 'Content of %s:\n' % (self._params['log-filename'], )
        text += open(self._params['log-filename']).read()
        text += ('-' * 80) + '\n'

        uptime = self._params['app-uptime']
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
        text += "Reportlab version: %s\n" % (reportlab.Version, )

        # Kiwi
        kiwi_version = '.'.join(map(str, kiwi.__version__.version))
        if hasattr(kiwi, 'library'):
            if hasattr(kiwi.library, 'get_revision'):
                kiwi_version += ' r' + kiwi.library.get_revision()
        text += "Kiwi version: %s\n" % (kiwi_version, )

        # Stoqdrivers
        stoqdrivers_version = '.'.join(map(str, stoqdrivers.__version__))
        if hasattr(stoqdrivers.library, 'get_revision'):
            stoqdrivers_version += ' r' + stoqdrivers.library.get_revision()
        text += "Stoqdrivers version: %s\n" % (stoqdrivers_version, )

        # Stoqlib version
        stoqlib_version = stoqlib.version
        if hasattr(stoqlib.library, 'get_revision'):
            stoqlib_version += ' r' + stoqlib.library.get_revision()
        text += "Stoqlib version: %s\n" % (stoqlib_version, )

        # Stoq version
        text += "%s version: %s\n" % (self._params['app-name'],
                                      self._params['app-version'])
        text += "Psycopg version: %20s\n" % (psycopg2.__version__, )
        try:
            conn = get_connection()
            text += "PostgreSQL version: %20s\n" % (
                conn.queryOne('SELECT version();'))
            conn.close()
        except StoqlibError:
            pass
        text += ('-' * 80) + '\n'
        return text

    def _show_report(self, data):
        r = json.loads(data)
        label = gtk.LinkButton(
            r['report-url'],
            _("Report %s successfully opened") % r['report'])
        self._dialog.vbox.pack_start(label)
        label.show()
        self._yes_button.set_label(_("Close"))
        self._yes_button.set_sensitive(True)

    def _on_report__errback(self, response, args):
        log.info('Failed to report bug: %r count=%d' % (args, self._count))
        if self._count < _N_TRIES:
            self._send_bugreport()
        else:
            label = gtk.Label(_("Failed to submit bugreport"))
            self._dialog.vbox.pack_start(label)
            label.show()
            self._yes_button.set_label(_("Close"))
            self._yes_button.set_sensitive(True)

        self._count += 1

    def _on_report__callback(self, response, data):
        self._show_report(data)

    def _send_bugreport(self):
        response = self._api.bug_report(self._report)
        response.whenDone(self._on_report__callback)
        response.ifError(self._on_report__errback)

    def run(self):
        response = self._dialog.run()
        if response == gtk.RESPONSE_NO:
            return False

        self._no_button.hide()
        self._yes_button.set_sensitive(False)
        self._yes_button.set_label(_('Sending...'))
        self._parent.destroy()

        self._send_bugreport()
        self._dialog.run()
        return True

def show_dialog(params, tracebacks):
    """Show a crash report dialog and exit the application
    @param: dictionary of parameters
    @tracebacks: list of tracebacks
    """
    parent = get_current_toplevel()
    crd = CrashReportDialog(parent, params, tracebacks)
    crd.run()
    raise SystemExit
