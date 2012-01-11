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

import gtk

from stoqlib.api import api
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.processview import ProcessView
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ImporterDialog(BasicDialog):
    size = (400, 300)
    title = _("Importer Dialog")

    def __init__(self, format, filename):
        BasicDialog.__init__(self)
        self._initialize(size=self.size, title=self.title)

        self.format = format
        self.filename = filename

        self._build_ui()
        self._execute()

    def _build_ui(self):
        self.main_label.set_text(_("Importing %s...") % (self.filename, ))
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
        self.process_view.connect('read-line', self._on_processview__readline)
        self.process_view.connect('finished', self._on_processview__finished)
        self.expander.add(self.process_view)
        self.process_view.show()

        self.disable_ok()

    def _execute(self):
        args = ['stoqdbadmin', 'import',
                '-t', self.format,
                '--import-filename', self.filename,
                '-v']
        args.extend(api.db_settings.get_command_line_arguments())
        self.process_view.execute_command(args)

    def _parse_process_line(self, line):
        LOG_CATEGORY = 'stoqlib.importer.create'
        log_pos = line.find(LOG_CATEGORY)
        if log_pos == -1:
            return
        line = line[log_pos + len(LOG_CATEGORY) + 1:]
        if line.startswith('ITEMS:'):
            value = 0
            self.n_items = int(line.split(':', 1)[1])
            text = _("Importing ...")
        elif line.startswith('IMPORTED-ITEMS:'):
            value = 1
            self.imported_items = int(line.split(':', 1)[1])
            text = _("Imported %d items ...") % (self.imported_items, )
        elif line.startswith('ITEM:'):
            item = float(line.split(':', 1)[1])
            value = item / self.n_items
            text = _("Importing item %d ...") % (item + 1, )
        else:
            return
        self.progressbar.set_fraction(value)
        self.progressbar.set_text(text)

    def _finish(self, returncode):
        if returncode:
            self.expander.set_expanded(True)
            warning(_("Something went wrong while trying to import"))
            return
        self.progressbar.set_text(_("Done, %d items imported, %d skipped") % (
            self.imported_items, self.n_items - self.imported_items))
        self.progressbar.set_fraction(1.0)
        self.enable_ok()

    def _on_processview__readline(self, view, line):
        self._parse_process_line(line)

    def _on_processview__finished(self, view, returncode):
        self._finish(returncode)


class ImporterProgressDialog(object):
    """ Progress Dialog for importing items """

    def __init__(self, format, filename):
        self.format = format
        self.filename = filename

        self._build_ui()
