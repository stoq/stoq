# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
""" Editors implementation for open/close operation on till operation"""

import datetime

from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.python import Settable

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BaseCashSlave(BaseEditorSlave):
    """A slave representing two fields, which is used by Cash editors:

    Date:        YYYY-MM-DD
    Cash Amount: [        ]
    """

    model_type = Settable
    gladefile = 'BaseCashSlave'
    proxy_widgets = ('value', 'balance')

    #
    # BaseEditorSlave
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, BaseCashSlave.proxy_widgets)
        self.date.set_text(str(datetime.date.today()))
        self.proxy.update('value', currency(0))

    #
    # Kiwi handlers
    #

    def on_value__validate(self, widget, value):
        zero = currency(0)
        if value <= zero:
            return ValidationError(_("Value cannot be zero or less than zero"))


class RemoveCashSlave(BaseCashSlave):

    def on_value__validate(self, widget, value):
        if value <= currency(0):
            return ValidationError(_("Value cannot be zero or less than zero"))
        if value > self.model.balance:
            return ValidationError(
                _("Value cannot be more than the total Till balance"))
