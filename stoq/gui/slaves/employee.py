# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
##  Author(s):      Daniel Saran R. da Cunha    <daniel@async.com.br>
##                  Henrique Romano             <henrique@async.com.br>
##                  Evandro Vale Miquelito      <evandro@async.com.br>
##                  Bruno Rafael Garcia         <brg@async.com.br>
##
"""
stoq/gui/slaves/employee.py

    Employee editor slaves implementation.
"""

import datetime
import gettext

import gtk
from kiwi.datatypes import currency
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.widgets.list import Column
from kiwi.datatypes import ValidationError
from stoqlib.gui.editors import BaseEditorSlave
from stoqlib.gui.dialogs import run_dialog
from stoqlib.gui.search import get_max_search_results

from stoq.lib.parameters import sysparam
from stoq.lib.validators import get_price_format_str
from stoq.domain.person import (WorkPermitData, MilitaryData, 
                                VoterData, EmployeeRole, EmployeeRoleHistory)
from stoq.domain.interfaces import IEmployee, ISalesPerson
from stoq.domain.account import BankAccount

_ = gettext.gettext


class EmployeeDetailsSlave(BaseEditorSlave):
    gladefile = 'EmployeeDetailsSlave'
    model_iface = IEmployee

    # 
    # Widgets specification for size groups.
    #

    left_widgets_group =  ('admission_date_label',
                           'registry_number_label',
                           'military_cert_serie_label',
                           'military_cert_category_label',
                           'military_cert_number_label',
                           'voter_id_number_label',
                           'voter_id_zone_label',
                           'voter_id_section_label',
                           'expire_vacation_label')

    right_widgets_group = ('person_dependent_number_label',
                           'education_level_label',
                           'pis_number_label',
                           'pis_registry_date_label',
                           'pis_bank_label',
                           'workpermit_number_label',
                           'workpermit_serie_label',
                           'bank_account_label',
                           'bank_label',
                           'bank_agency_label')

    #
    # Proxy widgets
    #

    employee_widgets =    ('admission_date',
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

    voter_widgets =       ('voter_id_number',
                           'voter_id_zone',
                           'voter_id_section')

    military_widgets =    ('military_doc_category',
                           'military_doc_serie',
                           'military_doc_number')

    def setup_widgets(self):
        self.right_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self.left_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        for widget in EmployeeDetailsSlave.left_widgets_group:
            w = getattr(self, widget)
            self.left_size_group.add_widget(w)

        for widget in EmployeeDetailsSlave.right_widgets_group:
            w = getattr(self, widget)
            self.right_size_group.add_widget(w)

    #
    # BaseEditorSlave hooks
    # 

    def setup_proxies(self):
        self.setup_widgets()

        assert(self.model)

        proxy_info = [
            ('workpermit_data',
             EmployeeDetailsSlave.work_permit_widgets, WorkPermitData),
            ('military_data',
             EmployeeDetailsSlave.military_widgets, MilitaryData),
            ('voter_data',
             EmployeeDetailsSlave.voter_widgets, VoterData),
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
    proxy_widgets = ('statuses_combo',)

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
                     'salary',)

    def __init__(self, conn, employee, edit_mode):
        self.max_results = get_max_search_results()
        self.employee = employee
        self.person = employee.get_adapted()
        self.salesperson = ISalesPerson(self.person, connection=conn)
        self.is_edit_mode = edit_mode
        self.current_role_history = self._get_active_role_history()
        BaseEditorSlave.__init__(self, conn)
 
    def _setup_entry_completion(self):
        roles = [role for role in
                 EmployeeRole.select(connection=self.conn)]
        roles = roles[:self.max_results]
        strings = [role.name for role in roles]
        self.role.set_completion_strings(strings, list(roles))

    def _setup_widgets(self):
        if self.salesperson:
            self.comission.update(self.salesperson.comission)
        self._setup_entry_completion()
        self.salary.set_data_format(get_price_format_str())

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
            self.salesperson.comission = self.comission.get_value()
        elif self.salesperson:
            if self.salesperson.is_active:
                self.salesperson.inactivate()
        
        self.employee.salary = self.model.salary
        if not self.model.role == self.employee.role:
            self.employee.role = self.model.role
            if self.current_role_history:
                self.current_role_history.salary = self.model.salary
                self.current_role_history.ended = datetime.datetime.now()
                self.current_role_history.is_active = False
        else:
            # XXX This will prevent problems in case that you can't update 
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
        # This will avoid the circular import
        from stoq.gui.editors.person import EmployeeRoleEditor
        model =  run_dialog(EmployeeRoleEditor, self, self.conn,
                            self.model.role)
        if model:
            self._setup_entry_completion()
            self.proxy.update('role')

    def on_salary__validate(self, widget, value):
        if value <= 0:
            return ValidationError("Salary must be greater than zero")

    def after_role__changed(self, widget):
        self._update_sensitivity()
        
    def _update_sensitivity(self):
        editor = True
        settings = False
        if self.role.get_text():
            editor = self.role.is_valid()
            if editor:
                settings = self._is_default_salesperson_role()
        else:
            self.model.role = None
        self.role_editor_button.set_sensitive(editor)
        self.comission.set_sensitive(settings)


class EmployeeRoleHistorySlave(SlaveDelegate):
    gladefile = "EmployeeRoleHistorySlave"

    def __init__(self, employee):
        self.employee = employee
        SlaveDelegate.__init__(self, gladefile=self.gladefile)
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
