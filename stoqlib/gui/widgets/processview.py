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
import os
import platform

import glib
import gtk
from kiwi.utils import gsignal

from stoqlib.lib.process import Process, PIPE

CHILD_TIMEOUT = 100  # in ms
N_BYTES = 4096  # a page


class ProcessView(gtk.ScrolledWindow):
    gsignal('read-line', str)
    gsignal('finished', object)

    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_NEVER,
                        gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.listen_stdout = True
        self.listen_stderr = False
        self._source_ids = []
        self._create_view()

    def _create_view(self):
        self._textview = gtk.TextView()
        self._textview.set_editable(False)
        self._textview.set_cursor_visible(False)
        self._textview.set_wrap_mode(gtk.WRAP_WORD)
        self._textview.set_property('width-request', 1)
        self.add(self._textview)
        self.show()
        self._textview.show()

    def _watch_fd(self, fd):
        try:
            import fcntl
            fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
        except ImportError:
            return
        source_id = glib.io_add_watch(fd, glib.IO_IN, self._io_watch)
        self._source_ids.append(source_id)

    def _io_watch(self, fd, cond):
        while True:
            try:
                data = fd.read(N_BYTES)
            except IOError as e:
                if e.errno == errno.EAGAIN:
                    break
                else:
                    raise
            if data == '':
                break
            for line in data.split('\n'):
                if line:
                    self.emit('read-line', line)
                    self.feed(line + '\r\n')
        return True

    def _check_child_finished(self):
        self.retval = self.proc.poll()
        finished = self.retval is not None
        if finished:
            self._finished()
        return not finished

    def _finished(self):
        for source_id in self._source_ids[:]:
            glib.source_remove(source_id)
            self._source_ids.remove(source_id)
        self.emit('finished', self.retval)

    def execute_command(self, args):
        self.feed('Executing: %s\r\n' % (' '.join(args)))
        kwargs = {}
        # On Windows you have to passin stdout/stdin = PIPE or
        # it will result in an invalid handle, see
        # * CR2012071248
        # * http://bugs.python.org/issue3905
        if self.listen_stdout or platform.system() == 'Windows':
            kwargs['stdout'] = PIPE
        if self.listen_stderr or platform.system() == 'Windows':
            kwargs['stderr'] = PIPE
        self.proc = Process(args, **kwargs)
        if self.listen_stdout:
            self._watch_fd(self.proc.stdout)
        if self.listen_stderr:
            self._watch_fd(self.proc.stderr)

        # We could probably listen to SIGCHLD here instead
        glib.timeout_add(CHILD_TIMEOUT, self._check_child_finished)

    def feed(self, line):
        tbuffer = self._textview.get_buffer()
        tbuffer.insert(tbuffer.get_end_iter(), line)
        self._textview.scroll_to_iter(tbuffer.get_end_iter(), 0.0, False, 0, 0)

    @property
    def terminal(self):
        return self._terminal
