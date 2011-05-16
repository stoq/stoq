# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

"""Process View a simple view of a process' stdout or stderr"""

import errno
import fcntl
import os
import subprocess

import glib
import gtk
from kiwi.utils import gsignal
import vte


CHILD_TIMEOUT = 100 # in ms
N_BYTES = 4096 # a page

class ProcessView(gtk.ScrolledWindow):
    gsignal('read-line', str)
    gsignal('finished', object)

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.listen_stdout = True
        self.listen_stderr = False
        self._source_ids = []
        self._create_terminal()

    def _create_terminal(self):
        self._terminal = vte.Terminal()
        self.add(self.terminal)
        self.show()
        self._terminal.show()

    def _watch_fd(self, fd):
        fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
        source_id = glib.io_add_watch(fd, glib.IO_IN, self._io_watch)
        self._source_ids.append(source_id)

    def _io_watch(self, fd, cond):
        while True:
            try:
                data = fd.read(N_BYTES)
            except IOError, e:
                if e.errno == errno.EAGAIN:
                    break
                else:
                    raise
            if data == '':
                return False
            for line in data.split('\n'):
                if line:
                    self.emit('read-line', line)
                    self.feed(line + '\r\n')
        return True

    def _check_child_finished(self):
        try:
            os.waitpid(self.proc.pid, os.WNOHANG)
        except OSError, e:
            if e.errno == errno.ECHILD:
                self._finished()
                return False
            else:
                raise

        return True

    def _finished(self):
        for source_id in self._source_ids:
            glib.source_remove(source_id)
        self.emit('finished', self.proc)

    def execute_command(self, args):
        self.feed('Executing: %s\r\n' % (' '.join(args)))
        kwargs = {}
        if self.listen_stdout:
            kwargs['stdout'] = subprocess.PIPE
        if self.listen_stderr:
            kwargs['stderr'] = subprocess.PIPE
        self.proc = subprocess.Popen(args, **kwargs)
        if self.listen_stdout:
            self._watch_fd(self.proc.stdout)
        if self.listen_stderr:
            self._watch_fd(self.proc.stderr)

        # We could probably listen to SIGCHLD here instead
        glib.timeout_add(CHILD_TIMEOUT, self._check_child_finished)

    def feed(self, line):
        self._terminal.feed(line)

    @property
    def terminal(self):
        return self._terminal
