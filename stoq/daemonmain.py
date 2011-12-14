#!/usr/bin/env python
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
## Author(s):   Stoq Team   <stoq-devel@async.com.br>
##
""" stoq-daemon: Daemon part of Stoq, ran on-demand.  """

import optparse
import os
import sys

from twisted.internet import reactor

from stoqlib.net.xmlrpcservice import XMLRPCService
from stoqlib.lib.osutils import get_application_dir
from stoq.lib.options import get_option_parser


class Daemon(object):
    def __init__(self, daemon_id):
        self._daemon_id = daemon_id
        self._start_xmlrpc()
        self._write_daemon_pids()

    def _start_xmlrpc(self):
        self._xmlrpc = XMLRPCService()
        self._xmlrpc.serve()

    def _write_daemon_pids(self):
        appdir = get_application_dir()
        daemondir = os.path.join(appdir, 'daemon', self._daemon_id)
        os.makedirs(daemondir)
        port = os.path.join(daemondir, 'port')
        open(port, 'w').write('%s\n' % (self._xmlrpc.port, ))

    def _check_active(self):
        if not self._xmlrpc.is_active():
            self.shutdown()

    def shutdown(self):
        reactor.stop()

    def run(self):
        print 'RUNNING DAEMON'
        reactor.callLater(5, self._check_active)
        reactor.run()


def main(args):
    parser = get_option_parser()
    group = optparse.OptionGroup(parser, 'Daemon')
    group.add_option('', '--daemon-id',
                      action="store",
                      dest="daemon_id",
                      help='Daemon Identifier')
    parser.add_option_group(group)
    options, args = parser.parse_args(args)
    if not options.daemon_id:
        raise SystemExit("Need a daemon id")

    daemon = Daemon(options.daemon_id)
    daemon.run()

if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        print 'Interrupted'
