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
from kiwi.datatypes import  ValidationError
from kiwi.ui.widgets.combo import ProxyComboBox

from stoqlib.domain.account import (Account, BankAccount,
                                    BillOption)
from stoqlib.gui.accounttree import AccountTree
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.boleto import (get_all_banks,
                                get_bank_info_by_number)
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class AccountEditor(BaseEditor):
    """ Account Editor """
    gladefile = "AccountEditor"
    proxy_widgets = ['description', 'code']
    size = (600, -1)
    model_type = Account

    def __init__(self, conn, model=None, parent_account=None):
        self._last_account_type = None
        self._bank_number = None
        self._bank_widgets = []
        self._bank_option_widgets = []
        self._option_fields = {}
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

        if self.model == sysparam(self.conn).IMBALANCE_ACCOUNT:
            self.account_type.set_sensitive(False)

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
        if self._bank_number is not None:
            self._save_bank()
        return self.model

    def _save_bank(self):
        if self.model.bank:
            bank = self.model.bank
            bank.set(account=self.model,
                     bank_number=int(self._bank_number),
                     bank_account=self._bank_account.get_text(),
                     bank_branch=self._bank_branch.get_text())
        else:
            bank = BankAccount(
                connection=self.conn,
                account=self.model,
                bank_number=int(self._bank_number),
                bank_account=self._bank_account.get_text(),
                bank_branch=self._bank_branch.get_text())
        self._save_bank_bill_options(bank)

    def _save_bank_bill_options(self, bank):
        for option, entry in self._option_fields.items():
            value = entry.get_text()
            bill_option = BillOption.selectOneBy(connection=self.conn,
                                                 bank_account=bank,
                                                 option=option)
            if bill_option is None:
                bill_option = BillOption(connection=self.conn,
                                         bank_account=bank,
                                         option=option,
                                         value=value)
            bill_option.value = value

    # Private

    def _add_widget(self, label, widget, options=False):
        n_rows = self.table.props.n_rows
        l = gtk.Label()
        l.set_markup(label)
        l.props.xalign = 1.0
        self.table.resize(n_rows + 1, 2)
        self.table.attach(
            l, 0, 1, n_rows, n_rows + 1,
            gtk.EXPAND | gtk.FILL, 0, 0, 0)
        self.table.attach(
            widget, 1, 2, n_rows, n_rows + 1,
            gtk.EXPAND | gtk.FILL, 0, 0, 0)
        if options:
            self._bank_option_widgets.extend([l, widget])
        else:
            self._bank_widgets.extend([l, widget])
        l.show()

    def _update_bank_type(self):
        self._remove_bank_option_widgets()

        self._bank_number_entry = gtk.Entry()
        self._bank_number_entry.set_sensitive(False)
        self._add_widget(_("Number:"), self._bank_number_entry, options=True)

        self._bank_branch = gtk.Entry()
        self._add_widget(_("Agency:"), self._bank_branch, options=True)
        self._bank_branch.show()

        self._bank_account = gtk.Entry()
        self._add_widget(_("Account:"), self._bank_account, options=True)
        self._bank_account.show()

        bank_number = self.bank_type.get_selected()
        if bank_number == None:
            return

        self._bank_number_entry.show()

        bank = get_bank_info_by_number(bank_number)
        self._bank_number_entry.set_text('%03d' % (int(bank_number), ))
        for option in bank.get_extra_options():
            entry = gtk.Entry()
            self._add_widget("<i>%s</i>:" % (option, ), entry, options=True)
            entry.show()
            self._option_fields[option] = entry

    def _fill_bank_account(self):
        if not self.model.bank:
            return

        self._bank_branch.set_text(self.model.bank.bank_branch)
        self._bank_account.set_text(self.model.bank.bank_account)

        bill_options = list(BillOption.selectBy(connection=self.conn,
                                                bank_account=self.model.bank))
        for bill_option in bill_options:
            if bill_option.option is None:
                continue
            field_entry = self._option_fields.get(bill_option.option)
            if field_entry:
                field_entry.set_text(bill_option.value)

    def _update_account_type(self, account_type):
        if not self.account_type.get_sensitive():
            return
        if account_type != Account.TYPE_BANK:
            self._remove_bank_widgets()
            self._remove_bank_option_widgets()
            self.code.set_sensitive(True)
            return
        self.code.set_sensitive(False)
        self.bank_type = ProxyComboBox()
        self._add_widget(_("Bank:"), self.bank_type)
        self.bank_type.connect('content-changed',
                               self._on_bank_type__content_changed)
        self.bank_type.show()

        banks = get_all_banks()
        self.bank_type.prefill(
            [(b.description,
              b.bank_number) for b in banks])

        if self.model.bank:
            try:
                self.bank_type.select(self.model.bank.bank_number)
            except KeyError:
                self.bank_type.select(None)

    def _remove_bank_widgets(self):
        for widget in self._bank_widgets:
            widget.parent.remove(widget)
            widget.destroy()
        self.table.resize(5, 2)
        self._bank_widgets = []

    def _remove_bank_option_widgets(self):
        for widget in self._bank_option_widgets:
            widget.parent.remove(widget)
            widget.destroy()
        self.table.resize(5 + len(self._bank_widgets) / 2, 2)
        self._bank_option_widgets = []
        self._option_fields = {}

    # Callbacks

    def _on_parent_accounts__selection_changed(self, objectlist, account):
        self.force_validation()

    def on_description__activate(self, entry):
        if self.validate_confirm():
            self.confirm()

    def on_description__validate(self, entry, text):
        if not text:
            return ValidationError(_("Account description cannot be empty"))

    def on_account_type__content_changed(self, account_type):
        account_type = account_type.get_selected()
        if self._last_account_type == account_type:
            return
        self._update_account_type(account_type)
        self._last_account_type = account_type

    def _on_bank_type__content_changed(self, bank_type):
        bank_number = bank_type.get_selected()
        if self._bank_number == bank_number:
            return
        self._update_bank_type()
        self._fill_bank_account()

        self._bank_number = bank_number
