# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2012 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Web Service APIs """

import datetime
import json
import os
import urllib
import platform
import sys

from zope.interface import implements
from kiwi.component import get_utility
from kiwi.log import Logger
from twisted.internet import reactor
from twisted.internet.defer import succeed, Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer

from stoqlib.database.runtime import get_connection
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.parameters import is_developer_mode, sysparam
from stoqlib.lib.pluginmanager import InstalledPlugin

log = Logger('stoqlib.webservice')


class JsonDownloader(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.data = ''

    def _try_show_html(self, data):
        if not data:
            return
        if not '<html>' in data:
            return
        if not is_developer_mode():
            return

        from stoqlib.gui.webview import show_html
        show_html(data)

    def dataReceived(self, bytes):
        self.data += bytes

    def connectionLost(self, reason):
        try:
            data = json.loads(self.data)
        except ValueError:
            self._try_show_html(self.data)
            log.info(self.data)
            data = None
        self.finished.callback(data)


class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

    def resumeProducing(self):
        pass


class WebService(object):
    API_SERVER = os.environ.get('STOQ_API_HOST', 'http://api.stoq.com.br')

    #
    #   Private API
    #

    def _get_headers(self):
        user_agent = 'Stoq'
        app_info = get_utility(IAppInfo, None)
        if app_info:
            user_agent += ' %s' % (app_info.get('version'), )
        headers = {'User-Agent': [user_agent]}

        return headers

    def _do_request(self, method, document, **params):
        url = '%s/%s' % (self.API_SERVER, document)
        headers = self._get_headers()

        if method == 'GET':
            # FIXME: Get rid of this
            if document in ['bugreport.json',
                            'tefrequest.json',
                            'version.json']:
                url += '?q=' + urllib.quote(json.dumps(params))
            else:
                url += '?' + urllib.urlencode(params)
            producer = None
        elif method == 'POST':
            producer = StringProducer(urllib.urlencode(params))
            headers['Content-Type'] = ['application/x-www-form-urlencoded']
        else:
            raise AssertionError(method)

        log.info("Requsting %s %s %r" % (method, url, headers))

        agent = Agent(reactor)
        d = agent.request(method, url, Headers(headers), producer)

        def dataReceived(response):
            finished = Deferred()
            response.deliverBody(JsonDownloader(finished))
            return finished
        d.addCallback(dataReceived)
        return d

    def _get_cnpj(self):
        # We avoid using SQLObject, otherwise crash-reporting will break
        # for errors that happens in patches modifying any of the
        # tables in the FROM clause below
        try:
            conn = get_connection()
        except StoqlibError:
            return ''
        data = conn.queryOne("""SELECT company.cnpj
          FROM parameter_data, branch, company, person
         WHERE field_name = 'MAIN_COMPANY' AND
               branch.id = field_value::int AND
               branch.person_id = person.id AND
               company.person_id = person.id;""")
        if data:
            return data[0]
        return ''

    #
    #   Public API
    #

    def version(self, conn, app_version):
        """Fetches the latest version
        :param conn: connection
        :param app_version: application version
        :returns: a deferred with the version_string as a parameter
        """
        params = {
            'dist': platform.dist(),
            'cnpj': self._get_cnpj(),
            'plugins': InstalledPlugin.get_plugin_names(conn),
            'time': datetime.datetime.today().isoformat(),
            'uname': platform.uname(),
            'version': app_version,
            'demo': sysparam(conn).DEMO_MODE,
        }
        return self._do_request('GET', 'version.json', **params)

    def bug_report(self, report):
        params = {
            'cnpj': self._get_cnpj(),
            'report': report,
        }
        if os.environ.get('STOQ_DISABLE_CRASHREPORT'):
            d = Deferred()
            print >> sys.stderr, params
            d.callback({'report-url': '<not submitted>',
                        'report': '<none>'})
            return d

        return self._do_request('POST', 'bugreport.json', **params)

    def tef_request(self, name, email, phone):
        params = {
            'name': name,
            'email': email,
            'phone': phone,
        }
        return self._do_request('GET', 'tefrequest.json', **params)

    def feedback(self, screen, email, feedback):
        app_info = get_utility(IAppInfo, None)
        if app_info:
            app_version = app_info.get('version')
        else:
            app_version = 'Unknown'
        conn = get_connection()
        params = {
            'cnpj': self._get_cnpj(),
            'demo': sysparam(conn).DEMO_MODE,
            'dist': platform.dist(),
            'email': email,
            'feedback': feedback,
            'plugins': InstalledPlugin.get_plugin_names(conn),
            'screen': screen,
            'time': datetime.datetime.today().isoformat(),
            'uname': platform.uname(),
            'version': app_version,
        }
        return self._do_request('GET', 'feedback.json', **params)
