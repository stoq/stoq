# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2017 Async Open Source <http://www.async.com.br>
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

from gi.repository import Gtk

from stoqlib.domain.service import Service
from stoq.lib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.services import SERVICE_LIST


class ServiceFiscalSlave(BaseEditorSlave):
    gladefile = 'ServiceFiscalSlave'
    model_type = Service
    proxy_widgets = ['service_list_combo', 'p_iss', 'city_taxation_code']

    def setup_proxies(self):
        self.service_list_combo.prefill([("{} - {}".format(
            code, desc), code) for code, desc in SERVICE_LIST.items()])

        self.p_iss.set_adjustment(Gtk.Adjustment(lower=0, upper=100, step_increment=0.5))
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)
