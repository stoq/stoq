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

import datetime

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.python import Settable

from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.paymenteditor import get_dialog_for_payment
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


# The reason for this is that SQLObject, even with lazyUpdates
# does create queries before sync() is called.
class _AccountTransactionTemporary(Settable):

    def get_other_account(self, unused):
        return self.source_account

    @classmethod
    def from_domain(cls, conn, transaction):
        return cls(code=transaction.code,
                   description=transaction.description,
                   date=transaction.date,
                   value=transaction.value,
                   conn=conn,
                   payment=transaction.payment,
                   account=transaction.account,
                   source_account=transaction.source_account,
                   transaction=transaction)

    def to_domain(self):
        fields = dict(code=self.code,
                      description=self.description,
                      date=self.date,
                      value=self.value,
                      account=self.account,
                      payment=self.payment,
                      source_account=self.source_account)
        if self.transaction:
            t = self.transaction
            for k, v in fields.items():
                setattr(t, k, v)
        else:
            t = AccountTransaction(connection=self.conn,
                                   **fields)

        return t


class AccountTransactionEditor(BaseEditor):
    """ Account Transaction Editor """
    gladefile = "AccountTransactionEditor"
    proxy_widgets = ['description', 'code', 'date', 'value']
    model_type = _AccountTransactionTemporary
    title = _("Account Editor")

    def __init__(self, conn, model, account):
        self.parent_account = account
        self.new = False
        if model is not None:
            model = _AccountTransactionTemporary.from_domain(conn, model)
            self.new = True
        BaseEditor.__init__(self, conn, model)

        payment_button = gtk.Button(_("Show Payment"))
        payment_button.connect("clicked", self._on_payment_button__clicked)
        box = self.main_dialog.action_area
        box.pack_start(payment_button, False, False)
        box.reorder_child(payment_button, 0)

        payment_button.set_sensitive(self.model.payment is not None)
        payment_button.show()


    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        return _AccountTransactionTemporary(
            transaction=None,
            conn=conn,
            code=u"",
            description=u"",
            value=currency(0),
            payment=None,
            date=datetime.datetime.today(),
            account=self.parent_account,
            source_account=sysparam(conn).IMBALANCE_ACCOUNT)

    def _setup_widgets(self):
        accounts = Account.select(connection=self.conn)
        items = [(a.long_description, a) for a in accounts]
        self.account.prefill(sorted(items))

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, AccountTransactionEditor.proxy_widgets)
        if self.model.account == self.parent_account:
            account = self.model.source_account
        else:
            account = self.model.account
        self.account.select(account)

    def validate_confirm(self):
        return self.model.value != 0

    def on_confirm(self):
        new_account = self.account.get_selected()
        at = self.model.to_domain()
        at.edited_account = new_account
        at.set_other_account(self.parent_account, new_account)
        return at

    def on_description__validate(self, entry, value):
        if value is None:
            return ValidationError(_("Description must be filled in"))

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

    def _on_payment_button__clicked(self, button):
        self._show_payment()

    def _show_payment(self):
        dialog_class = get_dialog_for_payment(self.model.payment)
        run_dialog(dialog_class, self,
                   self.conn, self.model.payment)
