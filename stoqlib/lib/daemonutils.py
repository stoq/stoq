# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2016 Async Open Source
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

import atexit
import logging
import threading

from stoqlib.lib.environment import is_developer_mode
from stoqlib.lib.threadutils import terminate_thread
from stoqlib.net.socketutils import get_random_port

_daemon = None
_event = threading.Event()
log = logging.getLogger(__name__)


class Daemon(threading.Thread):
    def __init__(self, port=None):
        super(Daemon, self).__init__()

        self.port = port
        if self.port is None and is_developer_mode():
            self.port = 8080
        elif self.port is None:
            self.port = get_random_port()
        # Indicate that this Thread is a daemon. Accordingly to the
        # documentation, the entire python program exits when no alive
        # non-daemon threads are left.
        self.daemon = True

    @property
    def running(self):
        return _event.wait()

    @property
    def server_uri(self):
        return 'http://localhost:%d' % (self.port, )

    def run(self):
        from stoqlib.net.webserver import run_server
        _event.set()
        run_server(self.port)

    def terminate(self):
        terminate_thread(self)


def start_daemon():
    global _daemon
    if _daemon is None:
        _daemon = Daemon()
        log.debug('Starting deamon')
        _daemon.start()
    return _daemon


@atexit.register
def stop_daemon():
    global _daemon
    if _daemon is not None and _daemon.isAlive():
        log.debug('Stopping deamon')
        _daemon.terminate()
    _daemon = None
