# -*- Mode: Python; coding: utf-8 -*-
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import BaseHTTPServer
import SimpleHTTPServer
import os
import urlparse

from kiwi.environ import environ

from stoqlib.net.calendarevents import CalendarEvents

_static = environ.get_resource_filename('stoq', 'html')
resources = {
    '/calendar-events': CalendarEvents(),
}


class _RequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        path = urlparse.urlparse(self.path)
        realpath = path.path
        args = urlparse.parse_qs(path.query)

        if realpath.startswith('/static'):
            # This will call translate_path bellow
            return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

        for name, resource in resources.iteritems():
            if realpath.startswith(name):
                # TODO: This is to keep compatibility with twisted api.
                # Maybe we should rewrite our handlers to use a different api
                self.args = args
                response = resource.render_GET(self)
                break
        else:
            self.send_error(404, "Resource not found")
            return

        self.send_response(200)
        # TODO: Right now we only have one resource, and it is returning
        # a json as the content. In the future we may want to support
        # other kinds of content types
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    #
    #  SimpleHTTPServer.SimpleHTTPRequestHandler
    #

    def translate_path(self, path):
        # SimpleHTTPRequestHandler calls this to translate the url path
        # into a filesystem path. It will always start with os.getcwd(),
        # which means we just need to replace it with the _static path
        translated = SimpleHTTPServer.SimpleHTTPRequestHandler.translate_path(
            # /static is just the endpoing name, the real path doesn't have it
            self, path.replace('/static', ''))
        return translated.replace(os.getcwd(), _static)

    def log_message(self, format, *args):
        # Be more quiet
        pass


def run_server(port):
    server = BaseHTTPServer.HTTPServer(('localhost', port), _RequestHandler)
    server.serve_forever()
