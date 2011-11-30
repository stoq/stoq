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

from kiwi.datatypes import  ValidationError

from stoqlib.domain.account import Account
from stoqlib.gui.accounttree import AccountTree
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class AccountEditor(BaseEditor):
    """ Account Editor """
    gladefile = "AccountEditor"
    proxy_widgets = ['description', 'code']
    size = (400, 300)
    model_type = Account

    def __init__(self, conn, model=None, parent_account=None):
        self.existing = model is not None
        self.parent_account = parent_account
        BaseEditor.__init__(self, conn, model)

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        return Account(description="",
                       account_type=Account.TYPE_CASH,
                       connection=conn)

    def _setup_widgets(self):
        self.parent_accounts = AccountTree(with_code=False, create_mode=True)
        self.parent_accounts.connect('selection-changed',
                                     self._on_parent_accounts__selection_changed)
        self.tree_box.pack_start(self.parent_accounts)
        self.tree_box.reorder_child(self.parent_accounts, 0)

        if not self.existing:
            ignore = self.model
        else:
            ignore = None

        self.account_type.prefill(Account.account_type_descriptions)
        account_type = self.model.account_type

        self.parent_accounts.insert_initial(self.conn, ignore=ignore)
        if self.parent_account:
            account = self.parent_accounts.get_account_by_id(
                self.parent_account.id)
            self.parent_accounts.select(account)
            if not self.existing:
                account_type = account.account_type
        self.account_type.select(account_type)
        self.parent_accounts.show()

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, AccountEditor.proxy_widgets)

    def validate_confirm(self):
        if not self.model.description:
            return False
        account = self.parent_accounts.get_selected()
        if not account:
            return True
        return account.selectable

    def on_confirm(self):
        new_parent = self.parent_accounts.get_selected()
        if new_parent:
            new_parent = new_parent.account
        if new_parent != self.model:
            self.model.parent = new_parent
        self.model.account_type = self.account_type.get_selected()
        return self.model

    def _on_parent_accounts__selection_changed(self, objectlist, account):
        self.force_validation()

    def on_description__activate(self, entry):
        if self.validate_confirm():
            self.confirm()

    def on_description__validate(self, entry, text):
        if not text:
            return ValidationError(_("Account description cannot be empty"))
