# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Henrique Romano           <henrique@async.com.br>
##
""" Invoice details editor implementation. This is a Brazil-specific
editor. """

from datetime import datetime

from kiwi.python import Settable

from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext as _

class InvoiceDetailsEditor(BaseEditor):
    gladefile = "InvoiceDetailsEditor"
    proxy_widgets = ("expedition_date",
                     "expedition_time")
    model_type = Settable

    def create_model(self, conn):
        dt = datetime.now()
        return Settable(date=dt.date(), time=dt.time())

    def get_title(self, dummy):
        return _("Edit Invoice Details")

    def get_proxy_widgets(self):
        return InvoiceDetailsEditor.proxy_widgets

    def setup_proxies(self):
        self.add_proxy(self.model, self.get_proxy_widgets())

    def on_confirm(self):
        return datetime.combine(self.model.date, self.model.time)
