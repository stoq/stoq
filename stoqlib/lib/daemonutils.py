# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import threading

from twisted.internet import defer, reactor
from twisted.web.xmlrpc import Proxy

from stoqlib.net.xmlrpcservice import XMLRPCService
from stoqlib.lib.environment import is_developer_mode
from stoqlib.lib.threadutils import terminate_thread


class Daemon(threading.Thread):
    def __init__(self, port=None):
        threading.Thread.__init__(self)

        self.port = port
        if self.port is None and is_developer_mode():
            self.port = 8080
        # Indicate that this Thread is a daemon. Accordingly to the
        # documentation, the entire python program exits when no alive
        # non-daemon threads are left.
        self.daemon = True
        self.running = False

    #
    #  Public API
    #

    def run(self):
        self._xmlrpc = XMLRPCService(self.port)
        self._xmlrpc.serve()

        self.port = self._xmlrpc.port
        self.running = True

    def stop(self):
        terminate_thread(self)
        self.port = None
        self.running = False


class DaemonManager(object):
    def __init__(self, port=None):
        self._port = port
        self._daemon = None

    def start(self):
        if self._daemon and self._daemon.port is not None:
            return defer.succeed(self)

        self._daemon = Daemon(port=self._port)
        self._daemon.start()

        reactor.callLater(0.1, self._check_active)
        self._defer = defer.Deferred()
        return self._defer

    def stop(self):
        if not self._daemon:
            return

        self._daemon.stop()

    def _check_active(self):
        if self._daemon is None or not self._daemon.running:
            reactor.callLater(0.1, self._check_active)
            return

        self._defer.callback(self)

    @property
    def base_uri(self):
        return 'http://localhost:%d' % (self._daemon.port, )

    def get_client(self):
        return Proxy('%s/XMLRPC' % (self.base_uri, ))


_daemon = DaemonManager()


def start_daemon():
    return _daemon.start()


def stop_daemon():
    _daemon.stop()
