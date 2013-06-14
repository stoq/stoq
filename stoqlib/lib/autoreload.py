# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source
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

import glib
import pyinotify

from stoqlib.lib.distutils import get_all_source_files
from stoq.gui.shell.shell import get_shell


class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        self._reload_filename(event.pathname)

    def _reload_filename(self, filename):
        shell = get_shell()
        app_name = shell.get_current_app_name()
        if app_name == "launcher":
            app_name = None
        shell.quit(restart=True, app=app_name)


def _autoreload_timeout(notifier):
    notifier.process_events()
    while notifier.check_events():
        notifier.read_events()
        notifier.process_events()
    return True


def install_autoreload():
    wm = pyinotify.WatchManager()
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler, timeout=10)

    files = list(get_all_source_files())
    wm.add_watch(files, pyinotify.IN_CLOSE_WRITE)

    glib.timeout_add(200, _autoreload_timeout, notifier)
