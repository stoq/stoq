# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##
# TODO: Authentication
# TODO: Log client requests to a file

"""xmlrpclib helpers/workarounds/bug fixes"""

import xmlrpclib
import SimpleXMLRPCServer

from kiwi.log import Logger
from kiwi.python import namedAny
from zope.interface import implements

from stoqlib.lib.interfaces import IXMLRPCService

log = Logger('stoqlib.xmlrpc')

# Monkey patch xmlrpclib which is broken in < Python 2.5
def dumps(real):
    def wrapper(*args, **kwargs):
        kwargs['allow_none'] = True
        return real(*args, **kwargs)
    return wrapper
xmlrpclib.dumps = dumps(xmlrpclib.dumps)

class Method(object):
    def __init__(self, method):
        self.method = method

    def __call__(self, *args, **kwargs):
        log.info('Sending %s command' % self.method.__name)

        # Attempt to recreate exception sent from the client side
        try:
            return self.method(*args, **kwargs)
        except xmlrpclib.Fault, e:
            raise
            # We receive the exception from xmlrplib as name:string
            exc_name, msg = e.faultString.split(":", 1)
            try:
                exc = namedAny(exc_name)
                raise exc(msg)
            except Exception, unused:
                # In case server/client side is out of sync
                raise Exception(msg)

# This is only done so we can do a try/except around a method call
class ServerProxy(xmlrpclib.ServerProxy):
    def __getattr__(self, name):
        return Method(xmlrpclib.ServerProxy.__getattr__(self, name))

class XMLRPCWebService(SimpleXMLRPCServer.SimpleXMLRPCServer):
    allow_reuse_address = True

class XMLRPCService(object):
    """An XMLRPCService using SimpleXMLRPCServer from the standard library
    """
    implements(IXMLRPCService)
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port

        self.service = XMLRPCWebService((hostname, port), logRequests=False)
        self.service.register_introspection_functions()
        self.service.register_instance(self)

    def serve(self):
        log.info("serve: Listening to port %s:%d" % (self.hostname or '*',
                                                     self.port))
        self.service.serve_forever()

    def stop(self):
        raise SystemExit
try:
    from twisted.web import xmlrpc, server
    from twisted.internet import reactor
    has_twisted = True
except ImportError:
    has_twisted = False

if has_twisted:
    class XMLRPCService(xmlrpc.XMLRPC):
        """An XMLRPCService using Twisted
        """
        implements(IXMLRPCService)
        def __init__(self, hostname, port):
            xmlrpc.XMLRPC.__init__(self)
            self._hostname = hostname
            self._port = port
            self._service = server.Site(self)

        def serve(self):
            log.info('Listening on port %d' % self._port)
            reactor.listenTCP(self._port, self._service)
            reactor.run()

        def stop(self):
            self._service.stopFactory()
            reactor.callLater(0, reactor.stop)
