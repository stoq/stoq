# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Henrique Romano             <henrique@async.com.br>
##
""" Basic slave definitions """

import gettext
import commands

import gtk
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.dialogs import save
from kiwi.python import Settable

from stoqlib.gui.base.editors import BaseEditorSlave
from stoqlib.reporting.utils import print_preview, build_report

_ = lambda msg: gettext.dgettext('stoqlib', msg)

class NoteSlave(BaseEditorSlave):
    """ Slave store general notes. The model must have an attribute 'notes'
    to work.
    """
    gladefile = 'NoteSlave'
    widgets = ('notes',)

    def __init__(self, conn, model):
        self.model = model
        self.model_type = self.model_type or type(model)
        BaseEditorSlave.__init__(self, conn, self.model)
        self.notes.set_accepts_tab(False)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.widgets)

class PrintDialogSlave(BaseEditorSlave):
    gladefile = 'PrintDialogSlave'
    proxy_widgets = ('printer_combo',
                     'filename_entry')
    model_type = Settable

    def __init__(self, report_class, *report_args, **report_kwargs):
        self._available_printers = []
        BaseEditorSlave.__init__(self, None, None)
        self._report_class = report_class
        self._report_kwargs = report_kwargs
        self._report_args = report_args
        self._update_view()

    def get_printer_name(self):
        if self.printer_radio.get_active():
            return self.model.printer_name
        return None

    def get_filename(self):
        if self.file_radio.get_active():
            return self.model.filename
        return None

    def get_report_file(self):
        return build_report(self._report_class, *self._report_args,
                            **self._report_kwargs)

    def _setup_printer_combo(self):
        self._available_printers = self._get_available_printers()
        if self._available_printers:
            self.printer_combo.prefill(self._available_printers)

    def _get_available_printers(self):
        printers = commands.getoutput("lpstat -d -a").split('\n')
        if printers:
            default_printer = printers[0].split(":", 1)[1].strip()
            return [p.split()[0].strip() for p in printers[1:]]
        return []

    def _setup_widgets(self):
        self._setup_printer_combo()

    def _update_view(self):
        if self._available_printers:
            is_active = self.printer_radio.get_active()
            self.filename_entry.set_sensitive(not is_active)
            self.file_selection_button.set_sensitive(not is_active)
            self.printer_combo.set_sensitive(is_active)
        else:
            self.printer_radio.set_sensitive(False)
            self.printer_combo.set_sensitive(False)

    #
    # BaseEditorSlave hooks
    #

    def create_model(self, dummy):
        return Settable(printer_name=None, filename='relat1.pdf')

    def get_title(self, dummy):
        return _("Print Dialog")

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, PrintDialogSlave.proxy_widgets)
        self._setup_widgets()

    #
    # Kiwi callbacks
    #

    def on_printer_radio__toggled(self, widget):
        self._update_view()

    def on_file_selection_button__clicked(self, *args):
        filename = save(_("Select the file"))
        if not filename:
            return
        self.filename_entry.set_text(filename)

    def on_print_preview_button__clicked(self, *args):
        print_preview(self.get_report_file())
