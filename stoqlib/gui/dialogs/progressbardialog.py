# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2013 Async Open Source
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

import gtk

from stoqlib.api import api
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.widgets.processview import ProcessView
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ProgressbarDialog(BasicDialog):
    """Dialogs showing progress of a ProcessView should inherit from this.
    """
    #: Default size for this dialog.
    size = (400, 300)

    #: Title for the window.
    title = None

    #: Default process and arguments to run.
    args = []

    #: Default output of the process running.
    log_category = None

    #: Message that will appear on the progressbar before the process is
    #: started.
    start_msg = _(u'Running task...')

    #: Message that will appear when process succeeds.
    success_msg = _(u'Task ran successfully!')

    #: Message that will appear then the process fails.
    failure_msg = _(u'Task failed!')

    def __init__(self, title=None, args=None, log_category=None,
                 start_msg=None, success_msg=None, failure_msg=None):
        """:param title: The title of the window.
        :param args: Default process and arguments to run.
        :param log_category: Default process and arguments to run.
        :param start_msg: Message that will appear on the progressbar before
        the process is started.
        :param success_msg: Message that will appear when process succeeds.
        :param failure_msg: Message that will appear then the process fails.
        """
        self.title = title or self.title
        if not self.title:
            raise ValueError('You must define a title for the window.')

        self.args = args or self.args
        if not self.args:
            raise ValueError('You must define the process and arguments for '
                             'the process.')

        self.log_category = log_category or self.log_category
        if not self.log_category:
            raise ValueError('You must define a log category to read the '
                             'output of the process from.')

        self.start_msg = start_msg or self.start_msg
        self.success_msg = success_msg or self.success_msg
        self.failure_msg = failure_msg or self.failure_msg

        BasicDialog.__init__(self, size=self.size, title=self.title)

        self._build_ui()
        self._execute()

    def _build_ui(self):
        self.main_label.set_text(self.start_msg)
        self.set_ok_label(_("Done"))

        self.progressbar = gtk.ProgressBar()
        self.vbox.pack_start(self.progressbar, False, False)
        self.progressbar.show()

        self.expander = gtk.Expander(label=_("Details..."))
        self.expander.set_expanded(False)
        self.vbox.pack_start(self.expander, True, True)
        self.expander.show()
        self.vbox.set_child_packing(self.main, False, False, 0, 0)

        self.process_view = ProcessView()
        self.process_view.listen_stdout = False
        self.process_view.listen_stderr = True
        self.expander.add(self.process_view)
        self.process_view.show()

        self.disable_ok()

    def _execute(self):
        self.args.extend(api.db_settings.get_command_line_arguments())
        self.process_view.execute_command(self.args)

    def _parse_process_line(self, line):
        log_pos = line.find(self.log_category)
        if log_pos == -1:
            return
        line = line[log_pos + len(self.log_category) + 1:]

        value, text = self.process_line(line)

        if value and text:
            self.progressbar.set_fraction(value)
            self.progressbar.set_text(text)

    def _finish(self, returncode):
        if returncode:
            self.expander.set_expanded(True)
            warning(self.failure_msg)
            return
        self.progressbar.set_text(self.success_msg)
        self.progressbar.set_fraction(1)
        self.enable_ok()

    #
    #   Public API
    #

    def process_line(self, line):
        """This method will be called once for each line of the process output,
        and must return a tuple containing the percentage and message that will
        be displayed in the progress bar.

        :param line: The line that must be processed.
        :returns: A tuple, in which in the first value is the percentage that
          will be displayed in the progressbar (0 <= value <= 1) and the text
          that will be displayed in it.
        """
        raise NotImplementedError("Can't define how to parse the output. You "
                                  "must implement process_line.")

    #
    #   Callbacks
    #

    def on_process_view__read_line(self, view, line):
        self._parse_process_line(line)

    def on_process_view__finished(self, view, returncode):
        self._finish(returncode)
