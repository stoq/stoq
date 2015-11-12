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
import logging
import os
import platform
import sys
import tempfile
import urllib
import urlparse

from kiwi.component import get_utility
from twisted.internet import reactor
from twisted.internet.defer import succeed, Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, HTTPDownloader
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from zope.interface import implementer

from stoqlib.database.runtime import get_default_store
from stoqlib.lib.environment import is_developer_mode
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.osutils import get_product_key
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import InstalledPlugin
from stoqlib.net.stoqlink import collect_link_statistics

log = logging.getLogger(__name__)


def get_main_cnpj(store):
    """Get the MAIN_COMPANY' cnpj without ORM interaction"""
    # We avoid using Storm, otherwise crash-reporting will break
    # for errors that happens in patches modifying any of the
    # tables in the FROM clause below
    result = store.execute("""
        SELECT company.cnpj
        FROM parameter_data, branch, company
        WHERE field_name = 'MAIN_COMPANY' AND
              branch.id::text = field_value AND
              branch.person_id = company.person_id;""")

    data = result.get_one()
    result.close()

    return data[0] if data else ''


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

        from stoqlib.gui.widgets.webview import show_html
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


@implementer(IBodyProducer)
class StringProducer(object):
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

    send_link_data = None

    #
    #   Private API
    #

    def _get_version(self):
        app_info = get_utility(IAppInfo, None)
        return app_info.get('version') if app_info is not None else 'Unknown'

    def _get_headers(self):
        user_agent = 'Stoq'
        app_info = get_utility(IAppInfo, None)
        if app_info:
            user_agent += ' %s' % (app_info.get('version'), )
        headers = {'User-Agent': [user_agent]}

        return headers

    def _do_request(self, method, document, callback=None, **params):
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
            # Avoid displaying an error window while we don't update
            # api.stoq.com.br with some new endpoints (or it is offline
            # for some reason).
            if response.code in [400, 401, 404, 500]:
                log.warning("%s request to '%s' returned %s",
                            method, url, response.code)
                return

            finished = Deferred()
            response.deliverBody(JsonDownloader(finished))
            return finished
        d.addCallback(dataReceived)
        if callback:
            d.addCallback(callback)
        return d

    def _do_download_request(self, document, callback=None, errback=None,
                             **params):
        url = '%s/%s?%s' % (
            self.API_SERVER, document, urllib.urlencode(params))
        headers = self._get_headers()
        file_ = tempfile.NamedTemporaryFile(delete=False)

        downloader = HTTPDownloader(
            url, file_.name, agent=headers['User-Agent'], headers=headers)

        def errback_(error):
            if errback is not None:
                code = getattr(downloader, 'status', None)
                errback(code, error)

        def callback_(res):
            if getattr(downloader, 'status', None) == '200' and callback:
                callback(file_.name)

            # Remove the temporary file after the callback has handled it
            os.remove(file_.name)

        downloader.deferred.addErrback(errback_)
        downloader.deferred.addCallback(callback_)

        parsed = urlparse.urlparse(url)
        reactor.connectTCP(parsed.netloc.split(':')[0],
                           parsed.port or 80, downloader)
        return downloader.deferred

    #
    #   Public API
    #

    def version(self, store, app_version):
        """Fetches the latest version
        :param store: a store
        :param app_version: application version
        :returns: a deferred with the version_string as a parameter
        """
        params = {
            'hash': sysparam.get_string('USER_HASH'),
            'demo': sysparam.get_bool('DEMO_MODE'),
            'dist': platform.dist(),
            'cnpj': get_main_cnpj(store),
            'plugins': InstalledPlugin.get_plugin_names(store),
            'product_key': get_product_key(),
            'time': datetime.datetime.today().isoformat(),
            'uname': platform.uname(),
            'version': app_version,
        }
        return self._do_request('GET', 'version.json', **params)

    def bug_report(self, report):
        params = {
            'hash': sysparam.get_string('USER_HASH'),
            'product_key': get_product_key(),
            'report': json.dumps(report)
        }
        if os.environ.get('STOQ_DISABLE_CRASHREPORT'):
            d = Deferred()
            sys.stderr.write(report)
            d.callback({'report-url': '<not submitted>',
                        'report': '<none>'})
            return d

        return self._do_request('POST', 'v2/bugreport.json', **params)

    def tef_request(self, name, email, phone):
        params = {
            'hash': sysparam.get_string('USER_HASH'),
            'name': name,
            'email': email,
            'phone': phone,
            'product_key': get_product_key(),
        }
        return self._do_request('GET', 'tefrequest.json', **params)

    def link_update(self, store):
        # Setup a callback (just in case we need it)
        def callback(response=False):
            """Send data to Stoq Server if the client is using Stoq Link"""
            if not response:
                # On falsy responses we will ignore the next send data
                WebService.send_link_data = False
                return
            # On non falsy responses we will send the next data right away
            WebService.send_link_data = True
            params = {
                'hash': key,
                'data': collect_link_statistics(store)
            }
            return self._do_request('POST', 'api/lite/data', **params)

        key = sysparam.get_string('USER_HASH')
        if WebService.send_link_data is False:
            # Don't even try to send data if the user is not using Stoq Link
            return None
        elif WebService.send_link_data:
            # If the instance is using stoq link lite, we may send data
            return callback(True)

        # If we dont know if the instance is using Stoq Link, we should ask
        # our server, and then send data in case it is using it.
        params = {
            'hash': key,
            'callback': callback,
        }
        return self._do_request('GET', 'api/lite/using', **params)

    def feedback(self, screen, email, feedback):
        default_store = get_default_store()
        params = {
            'hash': sysparam.get_string('USER_HASH'),
            'cnpj': get_main_cnpj(default_store),
            'demo': sysparam.get_bool('DEMO_MODE'),
            'dist': ' '.join(platform.dist()),
            'email': email,
            'feedback': feedback,
            'plugins': ', '.join(InstalledPlugin.get_plugin_names(default_store)),
            'product_key': get_product_key(),
            'screen': screen,
            'time': datetime.datetime.today().isoformat(),
            'uname': ' '.join(platform.uname()),
            'version': self._get_version(),
        }
        return self._do_request('GET', 'feedback.json', **params)

    def download_plugin(self, plugin_name, md5sum=None, callback=None):
        params = {
            'hash': sysparam.get_string('USER_HASH'),
            'plugin': plugin_name,
            'md5': md5sum or '',
            'version': self._get_version(),
        }

        def errback(code, error):
            if code == '204':
                log.info("No update needed. The plugin is already up to date.")
            else:
                return_messages = {
                    '400': "Plugin not available for this stoq version",
                    '404': "Plugin does not exist",
                    '405': "This instance has not acquired the specified plugin",
                }
                log.warning(return_messages.get(code, str(error)))

        return self._do_download_request(
            'api/eggs', callback=callback, errback=errback, **params)
