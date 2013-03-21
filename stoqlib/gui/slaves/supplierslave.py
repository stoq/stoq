# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
""" Supplier editor slaves implementation"""


from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.domain.person import Supplier


class SupplierDetailsSlave(BaseEditorSlave):
    model_type = Supplier
    gladefile = 'SupplierDetailsSlave'
    proxy_widgets = ('statuses_combo', 'product_desc')

    def setup_proxies(self):
        items = [(value, constant)
                 for constant, value in self.model_type.statuses.items()]
        self.statuses_combo.prefill(items)
        self.proxy = self.add_proxy(self.model,
                                    SupplierDetailsSlave.proxy_widgets)
