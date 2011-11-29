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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Client editor slaves implementation"""

from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.domain.interfaces import IClient
from stoqlib.domain.person import ClientCategory
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ClientStatusSlave(BaseEditorSlave):
    model_iface = IClient
    gladefile = 'ClientStatusSlave'

    proxy_widgets = ('statuses_combo', 'credit_limit',
                     'remaining_store_credit', 'category_combo')

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        category_list = ClientCategory.select(
            connection=self.conn).orderBy('name')
        category_items = [(cat.get_description(), cat) for cat in category_list]
        category_items.insert(0, ('', None))
        self.category_combo.prefill(category_items)
        table = self.model_type
        items = [(value, constant)
                    for constant, value in table.statuses.items()]
        self.statuses_combo.prefill(items)
        self.proxy = self.add_proxy(self.model,
                                    ClientStatusSlave.proxy_widgets)

    #
    # Kiwi Callbacks
    #

    def on_credit_limit__validate(self, entry, value):
        if value < 0:
            return ValidationError(
                         _("Credit limit must be greater than or equal to 0"))
