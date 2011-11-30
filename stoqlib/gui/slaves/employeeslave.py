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
""" Employee editor slaves implementation"""

import datetime

from kiwi.datatypes import currency
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.widgets.list import Column
from kiwi.datatypes import ValidationError

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.lib.parameters import sysparam
from stoqlib.domain.interfaces import IEmployee, ISalesPerson
from stoqlib.domain.account import BankAccount
from stoqlib.domain.person import (WorkPermitData, EmployeeRole,
                                   EmployeeRoleHistory)

_ = stoqlib_gettext


class EmployeeDetailsSlave(BaseEditorSlave):
    gladefile = 'EmployeeDetailsSlave'
    model_iface = IEmployee

    #
    # Proxy widgets
    #

    employee_widgets = ('admission_date',
                           'registry_number',
                           'expire_vacation',
                           'dependent_person_number',
                           'education_level')

    bank_account_widgets = ('name',
                            'account',
                            'branch')

    work_permit_widgets = ('workpermit_number',
                           'workpermit_serie',
                           'pis_number',
                           'pis_registry_date',
                           'pis_bank')

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):

        assert(self.model)

        proxy_info = [
            ('workpermit_data',
             EmployeeDetailsSlave.work_permit_widgets, WorkPermitData),
            ('bank_account',
             EmployeeDetailsSlave.bank_account_widgets, BankAccount)
        ]
        self.proxy = self.add_proxy(self.model,
                                    EmployeeDetailsSlave.employee_widgets)

        for name, widgets, table in proxy_info:
            obj = getattr(self.model, name)
            if not obj and table:
                obj = table(connection=self.conn)
            setattr(self.model, name, obj)
            self.add_proxy(obj, widgets)


class EmployeeStatusSlave(BaseEditorSlave):
    gladefile = 'EmployeeStatusSlave'
    model_iface = IEmployee
    proxy_widgets = ('statuses_combo', )

    def setup_proxies(self):
        items = [(v, c)
                    for c, v in self.model_type.statuses.items()]
        self.statuses_combo.prefill(items)
        self.proxy = self.add_proxy(self.model,
                                    EmployeeStatusSlave.proxy_widgets)


class EmployeeRoleSlave(BaseEditorSlave):
    gladefile = 'EmployeeRoleSlave'
    model_type = EmployeeRoleHistory
    proxy_widgets = ('role',
                     'salary', )

    def __init__(self, conn, employee, edit_mode, visual_mode=False):
        self.max_results = sysparam(conn).MAX_SEARCH_RESULTS
        self.employee = employee
        self.person = employee.person
        self.salesperson = ISalesPerson(self.person, None)
        self.is_edit_mode = edit_mode
        self.current_role_history = self._get_active_role_history()
        BaseEditorSlave.__init__(self, conn, visual_mode=visual_mode)

    def _setup_entry_completion(self):
        roles = EmployeeRole.select(connection=self.conn)
        items = [(role.name, role)
                 for role in roles.limit(self.max_results)]
        self.role.prefill(items)

    def _setup_widgets(self):
        self._setup_entry_completion()

    def _get_active_role_history(self):
        if self.is_edit_mode:
            return self.employee.get_active_role_history()
        else:
            return None

    def _is_default_salesperson_role(self):
        if (sysparam(self.conn).DEFAULT_SALESPERSON_ROLE ==
            self.model.role):
            return True
        return False

    def on_confirm(self):
        if self._is_default_salesperson_role():
            if self.salesperson:
                if not self.salesperson.is_active:
                    self.salesperson.activate()
            else:
                conn = self.conn
                self.salesperson = self.person.addFacet(ISalesPerson,
                                                        connection=conn)
        elif self.salesperson:
            if self.salesperson.is_active:
                self.salesperson.inactivate()

        old_salary = self.employee.salary
        self.employee.salary = self.model.salary
        if (self.model.role is not self.employee.role
            or old_salary != self.model.salary):
            self.employee.role = self.model.role
            if self.current_role_history:
                self.current_role_history.salary = old_salary
                self.current_role_history.ended = datetime.datetime.now()
                self.current_role_history.is_active = False
        else:
            # XXX This will prevent problems when you can't update
            # the connection.
            self.model_type.delete(self.model.id, connection=self.conn)
        return self.model

    #
    # BaseEditorSlave Hooks
    #

    def create_model(self, conn):
        return EmployeeRoleHistory(connection=conn,
                                   salary=self.employee.salary,
                                   role=self.employee.role,
                                   employee=self.employee)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    EmployeeRoleSlave.proxy_widgets)
        self._update_sensitivity()
        if not self.is_edit_mode:
            self.salary.set_text("")

    #
    # Kiwi handlers
    #

    def on_role_editor_button__clicked(self, *args):
        # This will avoid circular imports
        from stoqlib.gui.editors.personeditor import EmployeeRoleEditor
        model = run_dialog(EmployeeRoleEditor, self, self.conn,
                            self.model.role)
        if model:
            self._setup_entry_completion()
            self.proxy.update('role')

    def on_salary__validate(self, widget, value):
        if value <= 0:
            return ValidationError("Salary must be greater than zero")

    def after_role__content_changed(self, widget):
        self._update_sensitivity()

    def _update_sensitivity(self):
        editor = True
        if self.role.get_text():
            editor = self.role.is_valid()
        else:
            self.model.role = None
        self.role_editor_button.set_sensitive(editor)


class EmployeeRoleHistorySlave(GladeSlaveDelegate):
    gladefile = "EmployeeRoleHistorySlave"

    def __init__(self, employee):
        self.employee = employee
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self._setup_widgets()

    def _setup_widgets(self):
        self.history_list.set_columns(self._get_columns())
        self.history_list.add_list(self._get_objects())

    def _get_objects(self):
        return [result for result in self.employee.get_role_history()
                           if not result.is_active]

    def _get_columns(self):
        return [Column('began', _('Began'), data_type=datetime.date,
                       width=100),
                Column('ended', _('Ended'), data_type=datetime.date,
                       width=100, sorted=True),
                Column('role.name', _('Role'), data_type=str, width=200),
                Column('salary', _('Salary'), data_type=currency)]
