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
from kiwi.datatypes import ValidationError
from kiwi.ui.widgets.combo import ProxyComboBox
from kiwi.ui.widgets.entry import ProxyEntry

from stoqlib.api import api
from stoqlib.domain.account import (Account, BankAccount,
                                    BillOption)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.widgets.accounttree import AccountTree
from stoqlib.lib.boleto import (get_all_banks,
                                get_bank_info_by_number,
                                BoletoException)
from stoqlib.lib.message import info
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.boleto import BillTestReport

_ = stoqlib_gettext


class _Option(object):
    def __init__(self, option, value):
        self.option = option
        self.value = value


class _TemporaryBankAccount(object):
    def __init__(self):
        self.bank_number = 0
        self.bank_branch = u''
        self.bank_account = u''
        self._options = {}

    @property
    def options(self):
        return list(self._options.values())

    def set_option(self, option, value):
        self._options[option] = _Option(option, value)


class AccountEditor(BaseEditor):
    """ Account Editor """
    gladefile = "AccountEditor"
    proxy_widgets = ['description', 'code']
    model_type = Account
    model_name = _('Account')

    def __init__(self, store, model=None, parent_account=None):
        self._last_account_type = None
        self._bank_number = -1
        self._bank_widgets = []
        self._bank_option_widgets = []
        self._option_fields = {}
        self._test_button = None
        self.existing = model is not None
        self.parent_account = parent_account
        self.bank_model = _TemporaryBankAccount()
        BaseEditor.__init__(self, store, model)

        action_area = self.main_dialog.action_area
        action_area.set_layout(gtk.BUTTONBOX_END)
        action_area.pack_start(self._test_button, expand=False, fill=False)
        action_area.set_child_secondary(self._test_button, True)
        self._test_button.show()

    #
    # BaseEditor hooks
    #

    def create_model(self, store):
        return Account(description=u"",
                       account_type=Account.TYPE_CASH,
                       store=store)

    def _setup_widgets(self):
        self._test_button = gtk.Button(_("Print a test bill"))
        self._test_button.connect('clicked',
                                  self._on_test_button__clicked)
        self.parent_accounts = AccountTree(with_code=False, create_mode=True)
        self.parent_accounts.connect('selection-changed',
                                     self._on_parent_accounts__selection_changed)
        self.tree_box.pack_start(self.parent_accounts)
        self.tree_box.reorder_child(self.parent_accounts, 0)

        if sysparam.compare_object('IMBALANCE_ACCOUNT', self.model):
            self.account_type.set_sensitive(False)

        self.account_type.prefill(Account.account_type_descriptions)
        account_type = self.model.account_type

        self.parent_accounts.insert_initial(self.store,
                                            edited_account=self.model)
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
        self._save_bank()

    def refresh_ok(self, value):
        BaseEditor.refresh_ok(self, value)

        account_type = self.account_type.get_selected()
        if account_type != Account.TYPE_BANK:
            value = False
        self._test_button.set_sensitive(value)

    # Private

    def _save_bank(self):
        bank_account = self.model.bank
        if not bank_account:
            bank_account = BankAccount(account=self.model,
                                       store=self.store)
        # FIXME: Who sets this to a str?
        bank_account.bank_account = unicode(self.bank_model.bank_account)
        bank_account.bank_branch = unicode(self.bank_model.bank_branch)
        if self._bank_number is not None:
            bank_account.bank_number = self.bank_model.bank_number

        self._save_bank_bill_options(bank_account)

    def _save_bank_bill_options(self, bank_account):
        for option, entry in self._option_fields.items():
            value = unicode(entry.get_text())
            bill_option = self.store.find(BillOption,
                                          bank_account=bank_account,
                                          option=option).one()
            if bill_option is None:
                bill_option = BillOption(store=self.store,
                                         bank_account=bank_account,
                                         option=option,
                                         value=value)
            bill_option.value = value

    def _add_widget(self, label, widget, options=False):
        n_rows = self.table.props.n_rows
        l = gtk.Label()
        l.set_markup(label)
        l.props.xalign = 1.0
        self.table.resize(n_rows + 1, 2)
        self.table.attach(
            l, 0, 1, n_rows, n_rows + 1,
            gtk.FILL, 0, 0, 0)
        self.table.attach(
            widget, 1, 2, n_rows, n_rows + 1,
            gtk.EXPAND | gtk.FILL, 0, 0, 0)
        if options:
            self._bank_option_widgets.extend([l, widget])
        else:
            self._bank_widgets.extend([l, widget])
        l.show()
        return l

    def _update_bank_type(self):
        self._remove_bank_option_widgets()

        bank_number = self.bank_type.get_selected()
        bank_info = None
        if bank_number:
            bank_info = get_bank_info_by_number(bank_number)

        self.bank_number = ProxyEntry()
        self.bank_number.props.data_type = int
        self.bank_number.set_sensitive(False)
        bank_number_lbl = self._add_widget(api.escape(_("Number:")),
                                           self.bank_number, options=True)

        self.bank_branch = ProxyEntry()
        self.bank_branch.connect('validate', self._on_bank_branch__validate,
                                 bank_info)
        self.bank_branch.props.data_type = 'str'
        self.bank_branch.props.mandatory = True
        self.bank_branch.model_attribute = "bank_branch"
        bank_branch_lbl = self._add_widget(api.escape(_("Agency:")),
                                           self.bank_branch, options=True)
        if bank_number is not None:
            bank_branch_lbl.show()
            self.bank_branch.show()
        else:
            bank_branch_lbl.hide()

        self.bank_account = ProxyEntry()
        self.bank_account.connect('validate', self._on_bank_account__validate,
                                  bank_info)
        self._add_widget(api.escape(_("Account:")),
                         self.bank_account, options=True)
        self.bank_account.model_attribute = "bank_account"
        self.bank_account.props.data_type = 'str'
        if bank_number is not None:
            self.bank_account.props.mandatory = True
        self.bank_account.show()

        attributes = ['bank_account', 'bank_branch',
                      'bank_number']
        if bank_number is not None:
            bank_number_lbl.show()
            self.bank_number.show()

            self.bank_model.bank_number = bank_number

            for i, option in enumerate(bank_info.get_extra_options()):
                name = 'option' + str(i)
                entry = ProxyEntry()
                entry.model_attribute = name
                setattr(self, name, entry)
                # Set the model attr too so it can be validated
                setattr(self.bank_model, name, u'')
                entry.props.data_type = 'str'
                entry.connect('validate', self._on_bank_option__validate,
                              bank_info, option)
                self._add_widget("<i>%s</i>:" % (api.escape(option.capitalize()), ),
                                 entry, options=True)
                entry.show()
                self._option_fields[option] = entry
                attributes.append(entry.model_attribute)
        else:
            bank_number_lbl.hide()

        self.bank_proxy = self.add_proxy(
            self.bank_model, attributes)
        self._fill_bank_account()

    def _fill_bank_account(self):
        if not self.model.bank:
            return

        self.bank_model.bank_branch = self.model.bank.bank_branch.encode('utf-8')
        self.bank_model.bank_account = self.model.bank.bank_account.encode('utf-8')
        self.bank_proxy.update('bank_branch')
        self.bank_proxy.update('bank_account')

        bill_options = list(self.store.find(BillOption,
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
        self._add_widget(api.escape(_("Bank:")), self.bank_type)
        self.bank_type.connect('content-changed',
                               self._on_bank_type__content_changed)
        self.bank_type.show()

        banks = [(_('Generic'), None)]
        banks.extend([(b.description,
                       b.bank_number) for b in get_all_banks()])
        self.bank_type.prefill(banks)

        if self.model.bank:
            try:
                self.bank_type.select(self.model.bank.bank_number)
            except KeyError:
                self.bank_type.select(None)

        self._update_bank_type()

    def _remove_bank_widgets(self):
        for widget in self._bank_widgets:
            widget.get_parent().remove(widget)
            widget.destroy()
        self.table.resize(5, 2)
        self._bank_widgets = []

    def _remove_bank_option_widgets(self):
        for widget in self._bank_option_widgets:
            widget.get_parent().remove(widget)
            widget.destroy()
        self.table.resize(5 + len(self._bank_widgets) / 2, 2)
        self._bank_option_widgets = []
        self._option_fields = {}

    def _print_test_bill(self):
        try:
            bank_info = get_bank_info_by_number(self.bank_model.bank_number)
        except NotImplementedError:
            info(_("This bank does not support printing of bills"))
            return
        kwargs = dict(
            valor_documento=12345.67,
            data_vencimento=datetime.date.today(),
            data_documento=datetime.date.today(),
            data_processamento=datetime.date.today(),
            nosso_numero=u'24533',
            numero_documento=u'1138',
            sacado=[_(u"Drawee"), _(u"Address"), _(u"Details")],
            cedente=[_(u"Supplier"), _(u"Address"), _(u"Details"), ("CNPJ")],
            demonstrativo=[_(u"Demonstration")],
            instrucoes=[_(u"Instructions")],
            agencia=self.bank_model.bank_branch,
            conta=self.bank_model.bank_account,
        )
        for opt in self.bank_model.options:
            kwargs[opt.option] = opt.value
        data = bank_info(**kwargs)
        print_report(BillTestReport, data)

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

        self._bank_number = bank_number

    def _on_bank_branch__validate(self, entry, value, bank_info):
        if bank_info:
            try:
                bank_info.validate_field(value)
            except BoletoException as e:
                return ValidationError(str(e))

    def _on_bank_account__validate(self, entry, value, bank_info):
        if bank_info:
            try:
                bank_info.validate_field(value)
            except BoletoException as e:
                return ValidationError(str(e))

    def _on_bank_option__validate(self, entry, value, bank_info, option):
        try:
            bank_info.validate_option(option, value)
        except BoletoException as e:
            return ValidationError(str(e))
        self.bank_model.set_option(option, value)

    def _on_test_button__clicked(self, button):
        self._print_test_bill()


def test():  # pragma nocover
    creator = api.prepare_test()
    retval = run_dialog(AccountEditor, None, creator.store, None,
                        parent_account=None, visual_mode=True)
    creator.store.confirm(retval)


if __name__ == '__main__':  # pragma nocover
    test()
