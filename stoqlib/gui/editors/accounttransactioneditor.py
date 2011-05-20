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

from kiwi.datatypes import ValidationError

from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class AccountTransactionEditor(BaseEditor):
    """ Account Transaction Editor """
    gladefile = "AccountTransactionEditor"
    proxy_widgets = ['description', 'code', 'date', 'value']
    model_type = AccountTransaction

    def __init__(self, conn, model, account):
        self.parent_account = account
        BaseEditor.__init__(self, conn, model)

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        raise NotImplementedError

    def _setup_widgets(self):
        accounts = Account.select(connection=self.conn)
        items = [(a.long_description, a) for a in accounts]
        self.account.prefill(sorted(items))

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, AccountTransactionEditor.proxy_widgets)
        self.account.select(self.model.get_other_account(self.parent_account))

    def validate_confirm(self):
        return self.model.value != 0

    def on_confirm(self):
        new_account = self.account.get_selected()
        self.model.set_other_account(self.parent_account, new_account)
        return self.model

    def on_description__activate(self, entry):
        if self.validate_confirm():
            self.confirm()

    def on_code__activate(self, entry):
        if self.validate_confirm():
            self.confirm()

    def on_value__activate(self, entry):
        if self.validate_confirm():
            self.confirm()

    def on_value__validate(self, entry, value):
        if value == 0:
            return ValidationError(_("Value cannot be zero"))
