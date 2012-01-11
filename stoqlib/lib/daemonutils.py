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

import base64
import errno
import os
import signal
import shutil

from twisted.internet import defer, reactor
from twisted.web.xmlrpc import Proxy

from stoqlib.api import api
from stoqlib.lib.osutils import get_application_dir
from stoqlib.lib.process import Process


class TryAgainError(Exception):
    pass


def _get_random_id():
    return base64.urlsafe_b64encode(os.urandom(8))[:-1]


class DaemonManager(object):
    def __init__(self):
        self._daemon_id = _get_random_id()
        self._port = None
        self._process = None

    def start(self):
        try:
            self._get_port()
        except TryAgainError:
            pass
        else:
            return defer.succeed(self)

        args = ['stoq-daemon',
                '--daemon-id', self._daemon_id]
        args.extend(api.db_settings.get_command_line_arguments())
        self._process = Process(args)

        reactor.callLater(0.1, self._check_active)
        self._defer = defer.Deferred()
        return self._defer

    def stop(self):
        if not self._process:
            return
        os.kill(self._process.pid, signal.SIGINT)

        appdir = get_application_dir()
        daemondir = os.path.join(appdir, 'daemon', self._daemon_id)
        try:
            shutil.rmtree(daemondir)
        except OSError:
            pass

    def _get_port(self):
        appdir = get_application_dir()
        portfile = os.path.join(appdir, 'daemon', self._daemon_id, 'port')

        try:
            data = open(portfile).read()
        except IOError, e:
            if e.errno == errno.ENOENT:
                raise TryAgainError
            raise
        return int(data)

    def _check_active(self):
        try:
            port = self._get_port()
        except TryAgainError:
            reactor.callLater(0.1, self._check_active)
            return
        self._port = port
        self._defer.callback(self)

    @property
    def base_uri(self):
        return 'http://localhost:%d' % (self._port, )

    def get_client(self):
        return Proxy('%s/XMLRPC' % (self.base_uri, ))


_daemon = DaemonManager()


def start_daemon():
    return _daemon.start()


def stop_daemon():
    _daemon.stop()
