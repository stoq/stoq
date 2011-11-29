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

import datetime

from kiwi.datatypes import ValidationError
from kiwi.python import Settable

from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class FiscalMemoryDialog(BaseEditor):
    title = _("Print Fiscal Memory")
    model_type = Settable
    gladefile = 'FiscalMemoryEditor'
    proxy_widgets = ('start_date',
                     'end_date',
                     'start_reductions_number',
                     'end_reductions_number')

    def __init__(self, conn, printer):
        self._printer = printer
        BaseEditor.__init__(self, conn, model=None)
        self._toggle_sensitivity(True)

    def _toggle_sensitivity(self, date):
        for widget in (self.start_date, self.end_date):
            widget.set_sensitive(date)
        for widget in (self.start_reductions_number,
                       self.end_reductions_number):
            widget.set_sensitive(not date)

    #
    # BaseEditor
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    FiscalMemoryDialog.proxy_widgets)

    def on_confirm(self):
        if self.date_radio_button.get_active():
            self._printer.memory_by_date(
                self.model.start_date,
                self.model.end_date)
        else:
            self._printer.memory_by_reductions(
                self.model.start_reductions_number,
                self.model.end_reductions_number)

    def create_model(self, conn):
        return Settable(start_date=datetime.date.today(),
                        end_date=datetime.date.today(),
                        start_reductions_number=1,
                        end_reductions_number=1)

    #
    # callbacks
    #

    def on_reductions_radio_button__toggled(self, radio_button):
        self._toggle_sensitivity(False)

    def on_date_radio_button__toggled(self, radio_button):
        self._toggle_sensitivity(True)

    def on_start_date__validate(self, widget, date):
        if date > datetime.date.today():
            return ValidationError(_("Start date must be less than today"))
        if date > self.model.end_date:
            self.end_date.set_date(date)

    def on_end_date__validate(self, widget, date):
        if date > datetime.date.today():
            return ValidationError(_("End date must be less than today"))
        if date < self.model.start_date:
            self.start_date.set_date(date)

    def on_start_reductions_number__validate(self, widget, number):
        if number <= 0:
            return ValidationError(_("This number must be positive "
                                     "and greater than 0"))
        self.end_reductions_number.set_range(number, 9999)

    def on_end_reductions_number__validate(self, widget, number):
        if number <= 0:
            return ValidationError(_("This number must be positive "
                                     "and greater than 0"))
        if number < self.model.start_reductions_number:
            self.end_reductions_number.set_range(number, 9999)
