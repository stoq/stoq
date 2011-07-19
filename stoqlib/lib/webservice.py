# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
import platform
import urllib

import gobject
import gio
from kiwi.log import Logger

from stoqlib.domain.interfaces import ICompany
from stoqlib.database.runtime import get_connection
from stoqlib.lib.asyncresponse import AsyncResponse
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import InstalledPlugin

log = Logger('stoqlib.webservice')

class WebService(object):
    API_SERVER = os.environ.get('STOQ_API_HOST', 'http://api.stoq.com.br')

    #
    #   Private API
    #

    def _on_file_read_async(self, gfile, result, response):
        try:
            stream = gfile.read_finish(result)
        except gobject.GError, e:
            response.error(e)
            return

        self.data = ''
        stream.read_async(4096, self._on_stream_read_async, user_data=response)

    def _on_stream_read_async(self, stream, result, response):
        data = stream.read_finish(result)
        if not data:
            try:
                decoded = json.loads(self.data)
            except ValueError:
                log.debug('Error parsing json: %r' % (self.data, ))
                response.error(self.data)
                return
            response.done(decoded)
            return

        self.data += data
        stream.read_async(4096, self._on_stream_read_async, user_data=response)

    def _do_request(self, method_name, **params):
        response = AsyncResponse()
        url = '%s/%s?q=%s' % (
            self.API_SERVER, method_name, urllib.quote(json.dumps(params)))

        log.debug('Requesting: %r' % method_name)
        # GWinHttpRequest on Win32 is broken, do it synchronously instead.
        if platform.system() == 'Windows':
            import urllib2
            fd = urllib2.urlopen(url)
            data = fd.read()
            gobject.idle_add(lambda : response.done(data))
        else:
            gfile = gio.File(url)
            gfile.read_async(self._on_file_read_async, user_data=response)

        return response

    def _get_cnpj(self):
        # We avoid using SQLObject, otherwise crash-reporting will break
        # for errors that happens in patches modifying any of the
        # tables in the FROM clause below
        conn = get_connection()
        data = conn.queryOne("""SELECT person_adapt_to_company.cnpj
          FROM parameter_data,
               person_adapt_to_branch,
               person_adapt_to_company,
               person
         WHERE field_name = 'MAIN_COMPANY' AND
               person_adapt_to_branch.id = field_value::int AND
               person_adapt_to_branch.original_id = person.id AND
               person_adapt_to_company.original_id = person.id;""")
        if data:
            return data[0]
        return ''

    #
    #   Public API
    #

    def version(self, conn, app_version):
        """Fetches the latest version
        @param conn: connection
        @param app_version: application version
        @returns: an AsyncResponse object with the version_string as a parameter
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
        return self._do_request('version.json', **params)

    def bug_report(self, report):
        params = {
            'cnpj': self._get_cnpj(),
            'report': report,
        }
        if os.environ.get('STOQ_DISABLE_CRASHREPORT'):
            response = AsyncResponse()
            import sys
            print >> sys.stderr, params
            gobject.idle_add(lambda : response.done({
                'report-url': '<not submitted>',
                'report': '<none>'}))
            return response

        return self._do_request('bugreport.json', **params)

    def tef_request(self, name, email, phone):
        params = {
            'name': name,
            'email': email,
            'phone': phone,
        }
        return self._do_request('tefrequest.json', **params)
