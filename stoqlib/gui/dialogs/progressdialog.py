# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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

import glib
import gtk
from kiwi.ui.delegates import GladeDelegate
from kiwi.utils import gsignal


class ProgressDialog(GladeDelegate):
    """This is a dialog you use to show the progress of a certain task.
    It's just a label, progress bar and button.
    it'll always be displayed in the center of a screen.
    The progress is pulsating and updated every 100 ms.

    Signals:

    * *cancel* (): Emitted when a the cancel button is clicked

    """
    domain = 'stoq'
    gladefile = "ProgressDialog"
    toplevel_name = "ProgressDialog"

    gsignal('cancel')

    def __init__(self, label='', pulse=True):
        """
        Create a new ProgressDialog object.
        :param label: initial content of the label
        """
        GladeDelegate.__init__(self, gladefile=self.gladefile)
        self.set_title(label)
        self._pulse = pulse
        self._timeout_id = -1
        self._start_id = -1
        self.label.set_label(label)
        self.toplevel.set_position(gtk.WIN_POS_CENTER)

    def start(self, wait=50):
        """Start the task, it'll pulsate the progress bar until stop() is called
        :param wait: how many ms to wait before showing the dialog, defaults
          to 50
        """
        if self._pulse:
            self._timeout_id = glib.timeout_add(100, self._pulse_timeout)
        self._start_id = glib.timeout_add(wait, self._real_start)

    def stop(self):
        """Stops pulsating and hides the dialog
        """
        self.hide()
        if self._timeout_id != -1:
            glib.source_remove(self._timeout_id)
            self._timeout_id = -1
        if self._start_id != -1:
            glib.source_remove(self._start_id)
            self._start_id = -1

    def set_label(self, label):
        """Update the label of the dialog
        :param label: the new content of the label
        """
        self.label.set_label(label)

    #
    # Private and callbacks
    #

    def _real_start(self):
        self.show()
        # self.toplevel.present()
        self._start_id = -1
        return False

    def _pulse_timeout(self):
        self.progressbar.pulse()
        return True

    def on_cancel__clicked(self, button):
        self.emit('cancel')
        self.stop()
