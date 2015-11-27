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

import logging
import subprocess
import sys

from twisted.internet import reactor
from twisted.web import xmlrpc, server
from twisted.web.resource import Resource

from stoqlib.database.settings import db_settings
from stoqlib.lib.configparser import get_config
from stoqlib.net.socketutils import get_random_port

log = logging.getLogger(__name__)


class XMLRPCResource(xmlrpc.XMLRPC):
    def __init__(self, root):
        self._root = root
        xmlrpc.XMLRPC.__init__(self, allowNone=True)

    def xmlrpc_start_webservice(self):
        from stoqlib.net.webserver import WebResource
        self._root.putChild('web', WebResource())

    def xmlrpc_dbadmin(self, cmd_args, stdin=None):
        if sys.argv[0].endswith('.egg'):
            args = [sys.executable, sys.argv[0]]
        else:
            args = ['stoq']

        args.append('dbadmin')
        args.extend(cmd_args)

        config = get_config()
        for setting_opt, setting in [
                ('-H', db_settings.address),
                ('-d', db_settings.dbname),
                ('-f', config.filename),
                ('-p', db_settings.port and str(db_settings.port)),
                ('-u', db_settings.username),
                ('-w', db_settings.password)]:
            if setting:
                args.extend([setting_opt, setting])

        p = subprocess.Popen(args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p.communicate(input=stdin)


class XMLRPCService(server.Site):

    def __init__(self, port=None):
        self._port = port or get_random_port()
        self._addrs = []
        self._root = Resource()
        self._root.putChild('XMLRPC', XMLRPCResource(self._root))
        server.Site.__init__(self, self._root)

    def log(self, request):
        log.info('%s http://localhost:%d%s' % (request.method,
                                               self._port,
                                               request.uri))

    @property
    def port(self):
        return self._port

    def serve(self):
        log.info('Listening on port %d' % (self._port, ))
        reactor.listenTCP(self._port, self)

    def is_active(self):
        return len(self._addrs)

    def stop(self):
        self._service.stopFactory()
