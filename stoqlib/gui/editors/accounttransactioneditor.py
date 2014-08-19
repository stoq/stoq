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


class AccountTransactionEditor(BaseEditor):
    """ Account Transaction Editor """
    gladefile = "AccountTransactionEditor"
    proxy_widgets = ['description', 'code', 'date', 'value', 'is_incoming']
    model_type = AccountTransaction
    model_name = _('transaction')
    confirm_widgets = ['description', 'code', 'value']

    gsignal('account-added')

    def __init__(self, store, model, account):
        self.parent_account = store.fetch(account)
        self.new = False
        BaseEditor.__init__(self, store, model)

        payment_button = gtk.Button(_("Show Payment"))
        payment_button.connect("clicked", self._on_payment_button__clicked)
        box = self.main_dialog.action_area
        box.pack_start(payment_button, False, False)
        box.set_child_secondary(payment_button, True)
        box.set_layout(gtk.BUTTONBOX_END)

        # Setup the label, according to the type of transaction
        account_labels = Account.account_labels[account.account_type]
        self.is_incoming.set_label(account_labels[0])
        self.is_outgoing.set_label(account_labels[1])

        self.is_outgoing.set_active(self.model.source_account.id == account.id)

        payment_button.set_sensitive(self.model.payment is not None)
        payment_button.show()

    def create_model(self, store):
        return AccountTransaction(code=u"",
                                  description=u"",
                                  value=currency(0),
                                  payment=None,
                                  date=datetime.datetime.today(),
                                  account=sysparam.get_object(store, 'IMBALANCE_ACCOUNT'),
                                  source_account=self.parent_account,
                                  operation_type=AccountTransaction.TYPE_OUT,
                                  store=store)

    def _populate_accounts(self):
        accounts = self.store.find(Account)
        self.account.prefill(api.for_combo(
            accounts,
            attr='long_description'))

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
        account_transaction = self.model
        is_incoming = self.is_incoming.get_active()

        selected_account = self.account.get_selected()
        parent_account = self.parent_account
        if selected_account != account_transaction.get_other_account(parent_account):
            account_transaction.set_other_account(parent_account, selected_account)

        # Invert source and destination accounts. This is used to the source account
        # represent the outgoing value.
        if is_incoming and account_transaction.account != self.parent_account:
            account_transaction.invert_transaction_type()
        elif not is_incoming and account_transaction.source_account != self.parent_account:
            account_transaction.invert_transaction_type()

    def on_description__validate(self, entry, value):
        if value is None:
            return ValidationError(_("Description must be filled in"))

    def on_value__validate(self, entry, value):
        if value <= 0:
            return ValidationError(_("Value must be greater than zero"))

    def on_is_outgoing__toggled(self, *args):
        if self.is_outgoing.get_active():
            self.account_label.set_text(_(u"Destination:"))
        else:
            self.account_label.set_text(_(u"Source:"))

    def _on_payment_button__clicked(self, button):
        self._show_payment()

    def on_add_account__clicked(self, button):
        self._add_account()

    def _show_payment(self):
        dialog_class = get_dialog_for_payment(self.model.payment)
        run_dialog(dialog_class, self,
                   self.store, self.model.payment)

    def _add_account(self):
        store = api.new_store()
        parent_account = store.fetch(self.account.get_selected())
        model = run_dialog(AccountEditor, self, store,
                           parent_account=parent_account)
        if store.confirm(model):
            account = self.store.get(Account, model.id)
            self._populate_accounts()
            self.account.select(account)
            self.emit('account-added')
        store.close()


def test():  # pragma nocover
    creator = api.prepare_test()
    account = creator.create_account()
    retval = run_dialog(AccountTransactionEditor, None, creator.trans,
                        None, account)
    api.creator.trans.confirm(retval)


if __name__ == '__main__':  # pragma nocover
    test()
