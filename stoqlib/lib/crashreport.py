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
import hashlib
import logging
import sys
import time
import traceback
from twisted.internet import reactor
import os

import gobject
from kiwi.component import get_utility
from kiwi.utils import gsignal

try:
    import raven
    has_raven = True
except ImportError:
    has_raven = False

from stoqlib.database.runtime import get_default_store
from stoqlib.lib.environment import is_developer_mode
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.osutils import get_product_key
from stoqlib.lib.osutils import get_system_locale
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import InstalledPlugin
from stoqlib.lib.uptime import get_uptime
from stoqlib.lib.webservice import WebService, get_main_cnpj

log = logging.getLogger(__name__)
_tracebacks = []

_N_TRIES = 3


def _get_revision(module):
    if not hasattr(module, 'library'):
        return ''

    if not hasattr(module.library, 'get_revision'):
        return ''

    revision = module.library.get_revision()
    if revision is None:
        return ''
    return revision


def collect_report():
    report_ = {}

    # Date and uptime
    report_['date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_['tz'] = time.tzname
    report_['uptime'] = get_uptime()
    report_['locale'] = get_system_locale()

    # Python and System
    import platform
    report_['architecture'] = platform.architecture()
    report_['distribution'] = platform.dist()
    report_['python_version'] = tuple(sys.version_info)
    report_['system'] = platform.system()
    report_['uname'] = platform.uname()

    # Stoq application
    info = get_utility(IAppInfo, None)
    if info and info.get('name'):
        report_['app_name'] = info.get('name')
        report_['app_version'] = info.get('ver')

    # External dependencies
    import gtk
    report_['pygtk_version'] = gtk.pygtk_version
    report_['gtk_version'] = gtk.gtk_version

    import kiwi
    report_['kiwi_version'] = kiwi.__version__.version + (_get_revision(kiwi),)

    import psycopg2
    try:
        parts = psycopg2.__version__.split(' ')
        extra = ' '.join(parts[1:])
        report_['psycopg_version'] = tuple(map(int, parts[0].split('.'))) + (extra,)
    except:
        report_['psycopg_version'] = psycopg2.__version__

    import reportlab
    report_['reportlab_version'] = reportlab.Version.split('.')

    import stoqdrivers
    report_['stoqdrivers_version'] = stoqdrivers.__version__ + (
        _get_revision(stoqdrivers),)

    report_['product_key'] = get_product_key()

    try:
        from stoqlib.lib.kiwilibrary import library
        report_['bdist_type'] = library.bdist_type
    except Exception:
        pass

    # PostgreSQL database server
    try:
        from stoqlib.database.settings import get_database_version
        default_store = get_default_store()
        report_['postgresql_version'] = get_database_version(default_store)
        report_['plugins'] = InstalledPlugin.get_plugin_names(default_store)
        report_['demo'] = sysparam.get_bool('DEMO_MODE')
        report_['cnpj'] = get_main_cnpj(default_store)
    except Exception:
        pass

    # Tracebacks
    report_['tracebacks'] = {}
    for i, trace in enumerate(_tracebacks):
        t = ''.join(traceback.format_exception(*trace))
        # Eliminate duplicates:
        md5sum = hashlib.md5(t).hexdigest()
        report_['tracebacks'][md5sum] = t

    if info and info.get('log'):
        report_['log'] = open(info.get('log')).read()
        report_['log_name'] = info.get('log')

    return report_


def collect_traceback(tb, output=True, submit=False):
    """Collects traceback which might be submitted
    @output: if it is to be printed
    @submit: if it is to be submitted immediately
    """
    _tracebacks.append(tb)
    if output:
        traceback.print_exception(*tb)

    if has_raven and not is_developer_mode():  # pragma no cover
        extra = collect_report()
        extra.pop('tracebacks')

        sentry_url = os.environ.get(
            'STOQ_SENTRY_URL',
            ('http://89169350b0c0434895e315aa6490341a:'
             '0f5dce716eb5497fbf75c52fe873b3e8@sentry.stoq.com.br/4'))
        sentry_args = {}
        if 'app_version' in sentry_args:
            sentry_args['release'] = sentry_args['app_version']
        client = raven.Client(sentry_url, **sentry_args)

        # Don't sent logs to sentry
        if 'log' in extra:
            del extra['log']
        if 'log_name' in extra:
            del extra['log_name']

        tags = {}
        for name in ['architecture', 'cnpj', 'system', 'app_name', 'bdist_type',
                     'app_version', 'distribution', 'python_version',
                     'psycopg_version', 'pygtk_version', 'gtk_version',
                     'kiwi_version', 'reportlab_version',
                     'stoqdrivers_version', 'postgresql_version']:
            value = extra.pop(name, None)
            if value is None:
                continue

            if isinstance(value, (tuple, list)):
                chr_ = '.' if name.endswith('_version') else ' '
                value = chr_.join(str(v) for v in value)

            tags[name] = value

        client.captureException(tb, tags=tags, extra=extra)

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
    # This is only called if we are in developer mode
    rs = ReportSubmitter()
    d = rs.submit()
    while not d.called:
        reactor.iterate(delay=1)
