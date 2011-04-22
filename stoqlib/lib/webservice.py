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
import platform
import urllib

import gobject
import gio

from stoqlib.domain.interfaces import ICompany
from stoqlib.lib.asyncresponse import AsyncResponse
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import InstalledPlugin


class WebService(object):
    API_SERVER = "http://api.stoq.com.br/"

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
            response.done(self.data)
            return

        self.data += data
        stream.read_async(4096, self._on_stream_read_async, user_data=response)

    #
    #   Public API
    #

    def version(self, conn, app_version):
        """Fetches the latest version
        @param conn: connection
        @param app_version: application version
        @returns: an AsyncResponse object with the version_string as a parameter
        """
        branch = sysparam(conn).MAIN_COMPANY
        company = ICompany(branch.person)
        params = {
            'cnpj': company.cnpj,
            'dist': platform.dist(),
            'plugins': InstalledPlugin.get_plugin_names(conn),
            'time': datetime.datetime.today().isoformat(),
            'uname': platform.uname(),
            'version': app_version,
        }

        response = AsyncResponse()
        url = '%s/version.json?q=%s' % (
            self.API_SERVER, urllib.quote(json.dumps(params)))
        gfile = gio.File(url)
        gfile.read_async(self._on_file_read_async, user_data=response)
        return response

    def bug_report(self, report):
        response = AsyncResponse()
        url = '%s/bugreport.json?q=%s' % (
            self.API_SERVER, urllib.quote(json.dumps(report)))
        gfile = gio.File(url)
        gfile.read_async(self._on_file_read_async, user_data=response)
        return response
