# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import mock

from stoqlib.gui.dialogs.contactsdialog import ContactInfoListDialog
from stoqlib.gui.editors.personeditor import (BranchEditor, ClientEditor,
                                              EmployeeEditor, SupplierEditor,
                                              TransporterEditor, UserEditor)
from stoqlib.gui.search.callsearch import CallsSearch
from stoqlib.gui.search.creditcheckhistorysearch import CreditCheckHistorySearch
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.personwizard import PersonRoleWizard


class TestPersonRoleWizard(GUITest):
    @mock.patch('stoqlib.gui.templates.persontemplate.run_dialog')
    def test_run_dialog_parent(self, run_dialog):
        wizard = PersonRoleWizard(self.store, ClientEditor)
        self.click(wizard.next_button)
        step = wizard.get_current_step()
        person_slave = step.role_editor._person_slave

        buttons_dialogs = [
            (person_slave.calls_button, CallsSearch),
            (person_slave.contact_info_button, ContactInfoListDialog),
            (person_slave.credit_check_history_button, CreditCheckHistorySearch),
        ]

        for button, dialog in buttons_dialogs:
            run_dialog.reset_mock()
            self.click(button)
            self.assertEqual(run_dialog.call_count, 1)
            args = run_dialog.call_args[0]
            self.assertEqual(args, (dialog, wizard, step.store))

    def test_client(self):
        wizard = PersonRoleWizard(self.store, ClientEditor)

        step = wizard.get_current_step()
        self.check_wizard(wizard, 'wizard-client-person-role-type-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])

        step.person_slave.name.update('client name')
        step.person_slave.address_slave.street.update('street')
        step.person_slave.address_slave.streetnumber.update(123)
        step.person_slave.address_slave.district.update('district')

        self.assertSensitive(wizard, ['next_button'])
        self.click(wizard.next_button)

        client = wizard.retval
        self.check_wizard(wizard, 'wizard-client-person-role-finish',
                          [client, client.person] + list(client.person.addresses))

    def test_employee(self):
        employee = self.create_employee()
        employee.person.individual.cpf = u'954.181.357-75'
        employee.person.name = u'employee name'

        wizard = PersonRoleWizard(self.store, EmployeeEditor)

        step = wizard.get_current_step()
        step.person_document.update(employee.person.individual.cpf)
        self.check_wizard(wizard, 'wizard-employee-person-role-type-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])

        step.person_slave.name.update('new employee name')
        step.person_slave.address_slave.street.update('street')
        step.person_slave.address_slave.streetnumber.update(123)
        step.person_slave.address_slave.district.update('district')
        step.role_editor.role_slave.role.update(employee.role)
        step.role_editor.role_slave.salary.update(555)

        self.assertSensitive(wizard, ['next_button'])
        self.click(wizard.next_button)

        employee = wizard.retval
        self.check_wizard(wizard, 'wizard-employee-person-role-finish',
                          [employee, employee.person] + list(employee.person.addresses))

    def test_supplier(self):
        wizard = PersonRoleWizard(self.store, SupplierEditor)

        step = wizard.get_current_step()
        self.check_wizard(wizard, 'wizard-supplier-person-role-type-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])

        step.person_slave.name.update('supplier name')
        step.person_slave.address_slave.street.update('street')
        step.person_slave.address_slave.streetnumber.update(123)
        step.person_slave.address_slave.district.update('district')

        self.assertSensitive(wizard, ['next_button'])
        self.click(wizard.next_button)

        supplier = wizard.retval
        self.check_wizard(wizard, 'wizard-supplier-person-role-finish',
                          [supplier, supplier.person] + list(supplier.person.addresses))

    def test_branch(self):
        wizard = PersonRoleWizard(self.store, BranchEditor)

        step = wizard.get_current_step()
        self.check_wizard(wizard, 'wizard-branch-person-role-type-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])

        step.person_slave.name.update('branch name')
        step.person_slave.address_slave.street.update('street')
        step.person_slave.address_slave.streetnumber.update(123)
        step.person_slave.address_slave.district.update('district')

        self.assertSensitive(wizard, ['next_button'])
        self.click(wizard.next_button)

        branch = wizard.retval
        self.check_wizard(wizard, 'wizard-branch-person-role-finish',
                          [branch, branch.person] + list(branch.person.addresses))

    def test_transporter(self):
        wizard = PersonRoleWizard(self.store, TransporterEditor)

        step = wizard.get_current_step()
        self.check_wizard(wizard, 'wizard-transporter-person-role-type-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])

        step.person_slave.name.update(u'transporter name')
        step.person_slave.address_slave.street.update(u'street')
        step.person_slave.address_slave.streetnumber.update(123)
        step.person_slave.address_slave.district.update(u'district')

        self.assertSensitive(wizard, ['next_button'])
        self.click(wizard.next_button)

        transporter = wizard.retval
        self.check_wizard(wizard, 'wizard-transporter-person-role-finish',
                          [transporter, transporter.person] + list(transporter.person.addresses))

    def test_user(self):
        branch = self.create_branch()
        branch.person.company.fancy_name = u'branch'
        wizard = PersonRoleWizard(self.store, UserEditor)

        step = wizard.get_current_step()
        self.check_wizard(wizard, 'wizard-user-person-role-type-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])

        step.person_slave.name.update(u'user name')
        step.person_slave.address_slave.street.update(u'street')
        step.person_slave.address_slave.streetnumber.update(123)
        step.person_slave.address_slave.district.update(u'district')
        step.person_slave.address_slave.district.update(u'district')
        step.role_editor.user_details.username.update(u'username')
        step.role_editor.user_details.password_slave.password.update(u'foobar')
        step.role_editor.user_details.password_slave.confirm_password.update(u'foobar')
        step.role_editor.user_branches.target_combo.select_item_by_data(branch)
        step.role_editor.user_branches.add()

        self.assertSensitive(wizard, ['next_button'])
        self.click(wizard.next_button)

        user = wizard.retval
        self.check_wizard(wizard, 'wizard-user-person-role-finish',
                          [user, user.person] + list(user.person.addresses))
