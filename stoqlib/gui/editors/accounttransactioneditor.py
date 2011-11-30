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
from kiwi.utils import gsignal

from stoqlib.api import api
from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.accounteditor import AccountEditor
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
        value = currency(transaction.value)
        is_incoming = value > 0

        if not is_incoming:
            # FIXME: For some reason, (value * -1) and (value * currency(-1),
            #        both returns Decimal, but we need currency here.
            value *= -1
            value = currency(value)

        return cls(code=transaction.code,
                   description=transaction.description,
                   date=transaction.date,
                   value=value,
                   is_incoming=is_incoming,
                   conn=conn,
                   payment=transaction.payment,
                   account=transaction.account,
                   source_account=transaction.source_account,
                   transaction=transaction)

    def to_domain(self):
        if not self.is_incoming:
            self.value *= currency(-1)

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
    proxy_widgets = ['description', 'code', 'date', 'value', 'is_incoming']
    model_type = _AccountTransactionTemporary
    model_name = _('transaction')
    confirm_widgets = ['description', 'code', 'value']

    gsignal('account-added')

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

        # Setup the label, according to the type of transaction
        account_labels = Account.account_labels[account.account_type]
        self.is_incoming.set_label(account_labels[0])
        self.is_outgoing.set_label(account_labels[1])

        payment_button.set_sensitive(self.model.payment is not None)
        payment_button.show()

    def create_model(self, conn):
        return _AccountTransactionTemporary(
            transaction=None,
            conn=conn,
            code=u"",
            description=u"",
            is_incoming=True,
            value=currency(0),
            payment=None,
            date=datetime.datetime.today(),
            account=self.parent_account,
            source_account=sysparam(conn).IMBALANCE_ACCOUNT)

    def _populate_accounts(self):
        accounts = Account.select(connection=self.conn)
        items = [(a.long_description, a) for a in accounts]
        self.account.prefill(sorted(items))

    def _get_account(self):
        if self.model.account == self.parent_account:
            return self.model.source_account
        else:
            return self.model.account

    def setup_proxies(self):
        self._populate_accounts()
        self.add_proxy(self.model, AccountTransactionEditor.proxy_widgets)
        self.account.select(self._get_account())

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

    def on_value__validate(self, entry, value):
        if value <= 0:
            return ValidationError(_("Value must be greater than zero"))

    def _on_payment_button__clicked(self, button):
        self._show_payment()

    def on_add_account__clicked(self, button):
        self._add_account()

    def _show_payment(self):
        dialog_class = get_dialog_for_payment(self.model.payment)
        run_dialog(dialog_class, self,
                   self.conn, self.model.payment)

    def _add_account(self):
        trans = api.new_transaction()
        parent_account = trans.get(self.account.get_selected())
        model = run_dialog(AccountEditor, self, trans,
                           parent_account=parent_account)
        if api.finish_transaction(trans, model):
            account = Account.get(model.id, connection=self.conn)
            self._populate_accounts()
            self.account.select(account)
            self.emit('account-added')
        trans.close()
