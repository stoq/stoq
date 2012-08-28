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
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.search.clientsalaryhistorysearch import ClientSalaryHistorySearch
from stoqlib.domain.person import Client, ClientCategory, ClientSalaryHistory
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam

_ = stoqlib_gettext


class ClientStatusSlave(BaseEditorSlave):
    model_type = Client
    gladefile = 'ClientStatusSlave'

    proxy_widgets = ('statuses_combo', 'salary', 'credit_limit',
                     'remaining_store_credit', 'category_combo')

    def __init__(self, conn, model, visual_mode=False):
        BaseEditorSlave.__init__(self, conn, model, visual_mode)
        self._original_salary = self.model.salary

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        categories = ClientCategory.select(connection=self.conn)
        self.category_combo.prefill(api.for_combo(categories, empty=''))
        table = self.model_type
        items = [(value, constant)
                    for constant, value in table.statuses.items()]
        self.statuses_combo.prefill(items)
        self.proxy = self.add_proxy(self.model,
                                    ClientStatusSlave.proxy_widgets)

        self._setup_widgets()

    def _setup_widgets(self):
        salary_percentage = sysparam(self.conn).CREDIT_LIMIT_SALARY_PERCENT
        if salary_percentage > 0:
            self.credit_limit.set_sensitive(False)

    def on_confirm(self):
        if self.model.salary != self._original_salary:
            ClientSalaryHistory.add(self.conn, self._original_salary,
                                    self.model, api.get_current_user(self.conn))

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
                   self.get_toplevel().get_toplevel(), self.conn,
                   client=self.model)
