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

from stoqlib.api import api
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.creditdialog import CreditInfoListDialog
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.search.clientsalaryhistorysearch import ClientSalaryHistorySearch
from stoqlib.gui.utils.printing import print_report
from stoqlib.domain.person import Client, ClientCategory, ClientSalaryHistory
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.reporting.clientcredit import ClientCreditReport

_ = stoqlib_gettext


class ClientStatusSlave(BaseEditorSlave):
    model_type = Client
    gladefile = 'ClientStatusSlave'

    proxy_widgets = ('statuses_combo', 'category_combo')

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        categories = self.store.find(ClientCategory)
        self.category_combo.prefill(api.for_combo(categories, empty=''))
        table = self.model_type
        items = [(value, constant)
                 for constant, value in table.statuses.items()]
        self.statuses_combo.prefill(items)
        self.proxy = self.add_proxy(self.model,
                                    ClientStatusSlave.proxy_widgets)


class ClientCreditSlave(BaseEditorSlave):
    model_type = Client
    gladefile = 'ClientCreditSlave'

    proxy_widgets = ('salary', 'credit_limit', 'remaining_store_credit',
                     'credit_account_balance')

    def __init__(self, store, model, visual_mode=False, edit_mode=False):
        BaseEditorSlave.__init__(self, store, model, visual_mode, edit_mode)
        self._original_salary = self.model.salary

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    self.proxy_widgets)

        self._setup_widgets()

    def _setup_widgets(self):
        salary_percentage = sysparam.get_decimal('CREDIT_LIMIT_SALARY_PERCENT')
        if salary_percentage > 0:
            self.credit_limit.set_sensitive(False)

        # Only management can add credit to clients (in other words, users with
        # access to the Admin app).
        user = api.get_current_user(self.store)
        if not user.profile.check_app_permission(u'admin'):
            self.credit_transactions_button.hide()

    def on_confirm(self):
        if self.model.salary != self._original_salary:
            ClientSalaryHistory.add(self.store, self._original_salary,
                                    self.model, api.get_current_user(self.store))

    #
    # Kiwi Callbacks
    #

    def on_credit_limit__validate(self, entry, value):
        if value < 0:
            return ValidationError(
                _("Credit limit must be greater than or equal to 0"))

    def after_salary__changed(self, entry):
        self.proxy.update('remaining_store_credit')
        self.proxy.update('credit_limit')

    def on_salary__validate(self, widget, value):
        if value < 0:
            return ValidationError(
                _("Salary can't be lower than 0."))

    def after_credit_limit__changed(self, entry):
        self.proxy.update('remaining_store_credit')

    def on_salary_history_button__clicked(self, button):
        run_dialog(ClientSalaryHistorySearch,
                   self.get_toplevel().get_toplevel(), self.store,
                   client=self.model)

    def on_credit_transactions_button__clicked(self, button):
        # If we are not in edit mode, we are creating a new object, and thus we
        # should reuse the transaction
        reuse_store = not self.edit_mode
        run_dialog(CreditInfoListDialog, self.get_toplevel().get_toplevel(),
                   self.store, self.model, reuse_store=reuse_store)
        self.proxy.update('credit_account_balance')

    def on_print_credit_letter__clicked(self, button):
        print_report(ClientCreditReport, self.model)
