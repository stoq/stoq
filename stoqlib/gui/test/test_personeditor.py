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

import decimal

import mock

from kiwi.component import provide_utility

from stoqlib.api import api
from stoqlib.database.interfaces import ICurrentUser
from stoqlib.domain.person import LoginUser, Person, Employee
from stoqlib.gui.dialogs.contactsdialog import ContactInfoListDialog
from stoqlib.gui.editors.personeditor import (ClientEditor, UserEditor,
                                              EmployeeRoleEditor,
                                              EmployeeEditor, SupplierEditor,
                                              TransporterEditor, BranchEditor)
from stoqlib.gui.search.callsearch import CallsSearch
from stoqlib.gui.search.creditcheckhistorysearch import CreditCheckHistorySearch
from stoqlib.gui.test.uitestutils import GUITest, GUIDumper


class _BasePersonEditorTest(GUITest):
    editor = None

    @mock.patch('stoqlib.gui.templates.persontemplate.run_dialog')
    def test_run_dialog_parent(self, run_dialog):
        editor = self.editor(self.store, role_type=Person.ROLE_INDIVIDUAL)
        person_slave = editor._person_slave

        buttons_dialogs = [
            (person_slave.calls_button, CallsSearch),
            (person_slave.contact_info_button, ContactInfoListDialog),
        ]
        if self.editor == ClientEditor:
            # Only ClientEditor has this button
            buttons_dialogs.append(
                (person_slave.credit_check_history_button,
                 CreditCheckHistorySearch))

        for button, dialog in buttons_dialogs:
            run_dialog.reset_mock()
            self.click(button)
            self.assertEqual(run_dialog.call_count, 1)
            args = run_dialog.call_args[0]
            self.assertEqual(args, (dialog, editor, editor.store))


class TestClientEditor(_BasePersonEditorTest):
    editor = ClientEditor

    def test_queries(self):
        client = self.create_client()

        with self.count_tracer() as tracer:
            ClientEditor(self.store, client,
                         role_type=Person.ROLE_INDIVIDUAL)

        # FIXME: The list bellow is broken. It's documenting 26 queries but
        # only 21 are being executed. Maybe we should compare the queries
        # (with something like assertRaisesRegexp for parts like uuids)
        # instead of counting them. It will be easier to maintain.
        # NOTE: Document increases/decreases
        # 1: select user/branch/station (normally cached)
        # 4: transaction_entry
        # 4: insert person/individual/client/address
        # 1: select individual
        # 2: select company
        # 1: select address
        # 1: select client
        # 1: select client category
        # 1: select ui form
        # 1: select address
        # 4: select city location
        # 1: update individual
        # 2: select payment
        # 1: select current user
        # 1: select app permissions for the user
        self.assertEquals(tracer.count, 21)

    def test_create_individual(self):
        editor = ClientEditor(self.store, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-client-individual-create')

    def test_create_company(self):
        editor = ClientEditor(self.store, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-client-company-create')

    @mock.patch('stoqlib.gui.templates.persontemplate.warning')
    def test_edit_without_address(self, warning):
        client = self.create_client()
        editor = ClientEditor(self.store, client,
                              role_type=Person.ROLE_INDIVIDUAL)
        self.click(editor.get_person_slave().address_button)

        warning.assert_called_once_with(
            'You must define a valid main address before\n'
            'adding additional addresses')

    @mock.patch('stoqlib.gui.templates.persontemplate.warning')
    def test_edit_address(self, warning):
        client = self.store.find(Person,
                                 name=u"Franciso Elisio de Lima Junior")[0].client
        editor = ClientEditor(self.store, client,
                              role_type=Person.ROLE_INDIVIDUAL)

        dump = GUIDumper()
        dump.dump_editor(editor)

        def run_dialog2(dialog, parent, *args, **kwargs):
            d = dialog(*args, **kwargs)
            dump.dump_dialog(d)
            # Avoid committing
            return False

        def run_dialog(dialog, parent, *args, **kwargs):
            d = dialog(*args, **kwargs)
            dump.dump_dialog(d)
            with mock.patch('stoqlib.gui.base.lists.run_dialog',
                            new=run_dialog2):
                self.click(d.list_slave.listcontainer.add_button)
            return d.retval

        with mock.patch('stoqlib.gui.templates.persontemplate.run_dialog',
                        new=run_dialog):
            self.click(editor.get_person_slave().address_button)

        self.check_filename(dump, 'editor-client-edit-address')

    def test_only_admin_can_add_client_credit(self):
        client = self.create_client()
        editor = ClientEditor(self.store, client,
                              role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'client-editor-admin-user')

        admin_user = api.get_current_user(self.store)
        salesperson_user = self.store.find(LoginUser, username=u'elias').one()
        provide_utility(ICurrentUser, salesperson_user, replace=True)
        editor = ClientEditor(self.store, client,
                              role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'client-editor-salesperson-user')
        provide_utility(ICurrentUser, admin_user, replace=True)


class TestUserEditor(_BasePersonEditorTest):
    editor = UserEditor

    def test_create_individual(self):
        editor = UserEditor(self.store, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-user-individual-create')

    def test_create_company(self):
        editor = UserEditor(self.store, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-user-company-create')


class TestEmployeeEditor(_BasePersonEditorTest):
    editor = EmployeeEditor

    def test_create_individual(self):
        branch = self.create_branch()
        role = self.create_employee_role()

        editor = EmployeeEditor(self.store, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-employee-individual-create-empty')

        individual_slave = editor._person_slave
        address_slave = editor._person_slave.address_slave
        employee_role_slave = editor.role_slave

        individual_slave.name.update('name foo')
        address_slave.street.update('street foo')
        address_slave.streetnumber.update(800)
        address_slave.district.update('district foo')
        employee_role_slave.role.update(role)
        employee_role_slave.salary.update(decimal.Decimal('50'))

        details_slave = editor.details_slave
        details_slave.branch_combo.update(branch)

        self.click(editor.main_dialog.ok_button)
        self.check_editor(editor, 'editor-employee-individual-create-confirmed',
                          [editor.retval, branch])

    def test_create_company(self):
        editor = EmployeeEditor(self.store, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-employee-company-create')

    def test_update_status(self):
        employee = self.create_employee()
        sales_person = self.create_sales_person()
        employee.person.sales_person = sales_person
        sales_person.is_active = False
        editor = EmployeeEditor(self.store, role_type=Person.ROLE_INDIVIDUAL,
                                model=employee)

        individual_slave = editor._person_slave
        address_slave = editor._person_slave.address_slave
        employee_role_slave = editor.role_slave

        individual_slave.name.update('name foo')
        address_slave.street.update('street foo')
        address_slave.streetnumber.update(800)
        address_slave.district.update('district foo')
        employee_role_slave.salary.update(decimal.Decimal('50'))

        editor.status_slave.statuses_combo.update(Employee.STATUS_NORMAL)
        self.click(editor.main_dialog.ok_button)
        self.assertTrue(sales_person.is_active)


class TestSupplierEditor(_BasePersonEditorTest):
    editor = SupplierEditor

    def test_create_individual(self):
        editor = SupplierEditor(self.store, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-supplier-individual-create')

    def test_create_company(self):
        editor = SupplierEditor(self.store, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-supplier-company-create')


class TestTransporterEditor(_BasePersonEditorTest):
    editor = TransporterEditor

    def test_create_individual(self):
        editor = TransporterEditor(
            self.store, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(
            editor, 'editor-transporter-individual-create')

    def test_create_company(self):
        editor = TransporterEditor(
            self.store, role_type=Person.ROLE_COMPANY)
        self.check_editor(
            editor, 'editor-transporter-company-create')


class TestBranchEditor(_BasePersonEditorTest):
    editor = BranchEditor

    def test_create_individual(self):
        editor = BranchEditor(self.store, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-branch-individual-create')

    def test_create_company(self):
        editor = BranchEditor(self.store, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-branch-company-create')

    def test_edit_company(self):
        branch = api.sysparam.get_object(self.store, 'MAIN_COMPANY')
        editor = BranchEditor(self.store, branch, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-branch-edit')


class TestEmployeeRoleEditor(GUITest):
    def test_create(self):
        editor = EmployeeRoleEditor(self.store)
        self.check_editor(editor, 'editor-employeerole-create')
