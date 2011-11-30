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
""" Crash report logic """

import datetime
import platform
import sys
import time
import traceback
from twisted.internet import reactor

import gobject
from kiwi.component import get_utility
from kiwi.log import Logger
from kiwi.utils import gsignal

from stoqlib.exceptions import StoqlibError
from stoqlib.database.runtime import get_connection
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.parameters import sysparam, is_developer_mode
from stoqlib.lib.uptime import get_uptime
from stoqlib.lib.webservice import WebService

log = Logger('stoqlib.crashreporter')
_tracebacks = []

_N_TRIES = 3


def collect_report():
    info = get_utility(IAppInfo, None)

    text = ""
    text += "Report generated at %s %s\n" % (
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        ' '.join(time.tzname))
    text += ('-' * 80) + '\n'

    for i, (exctype, value, tb) in enumerate(_tracebacks):
        text += '\n'.join(traceback.format_exception(exctype, value, tb))
        if i != len(_tracebacks) - 1:
            text += '-' * 60
    text += ('-' * 80) + '\n'

    if info and info.get('log'):
        text += 'Content of %s:\n' % (info.get('log'), )
        text += open(info.get('log')).read()
        text += ('-' * 80) + '\n'

    uptime = get_uptime()
    text += "Application uptime: %dh%dmin\n" % (uptime / 3600,
                                                (uptime % 3600) / 60)
    text += "System: %r (%s)\n" % (platform.system(),
                                   ' '.join(platform.uname()))
    text += "Distribution: %s\n" % (' '.join(platform.dist()), )
    text += "Architecture: %s\n" % (' '.join(platform.architecture()), )

    text += "Python version: %r (%s)\n" % (
        '.'.join(map(str, sys.version_info)),
        platform.python_implementation())
    import gtk
    text += "PyGTK version: %s\n" % ('.'.join(map(str, gtk.pygtk_version)), )
    text += "GTK version: %s\n" % ('.'.join(map(str, gtk.gtk_version)), )
    import reportlab
    text += "Reportlab version: %s\n" % (reportlab.Version, )

    # Kiwi
    import kiwi
    kiwi_version = '.'.join(map(str, kiwi.__version__.version))
    if hasattr(kiwi, 'library'):
        if hasattr(kiwi.library, 'get_revision'):
            revision = kiwi.library.get_revision()
            if revision is not None:
                kiwi_version += ' r' + revision
    text += "Kiwi version: %s\n" % (kiwi_version, )

    # Stoqdrivers
    import stoqdrivers
    stoqdrivers_version = '.'.join(map(str, stoqdrivers.__version__))
    if hasattr(stoqdrivers.library, 'get_revision'):
            revision = stoqdrivers.library.get_revision()
            if revision is not None:
                stoqdrivers_version += ' r' + revision
    text += "Stoqdrivers version: %s\n" % (stoqdrivers_version, )

    # App version
    if info and info.get('name'):
        text += "%s version: %s\n" % (info.get('name'),
                                      info.get('version'))

    # Psycopg / Postgres
    import psycopg2
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


def collect_traceback(tb, output=True, submit=False):
    """Collects traceback which might be submitted
    @output: if it is to be printed
    @submit: if it is to be submitted immediately
    """
    _tracebacks.append(tb)

    if output:
        traceback.print_exception(*tb)

    if is_developer_mode() and submit:
        report()


def has_tracebacks():
    return bool(_tracebacks)


class ReportSubmitter(gobject.GObject):
    gsignal('failed', object)
    gsignal('submitted', object)

    def __init__(self):
        gobject.GObject.__init__(self)

        self._api = WebService()
        self._report = collect_report()
        self._count = 0

    def _done(self, args):
        self.emit('submitted', args)

    def _error(self, args):
        self.emit('failed', args)

    @property
    def report(self):
        return self._report

    def submit(self):
        response = self._api.bug_report(self._report)
        response.addCallback(self._on_report__callback)
        response.addErrback(self._on_report__errback)
        return response

    def _on_report__callback(self, data):
        log.info('Finished sending bugreport: %r' % (data, ))
        self._done(data)

    def _on_report__errback(self, failure):
        log.info('Failed to report bug: %r count=%d' % (failure, self._count))
        if self._count < _N_TRIES:
            self.submit()
        else:
            self._error(failure)
        self._count += 1


def report():
    conn = get_connection()
    if not sysparam(conn).ONLINE_SERVICES:
        return
    rs = ReportSubmitter()
    d = rs.submit()
    while not d.called:
        reactor.iterate(delay=1)
