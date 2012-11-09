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

from stoqlib.domain.person import Person
from stoqlib.gui.dialogs.liaisondialog import LiaisonListDialog
from stoqlib.gui.editors.personeditor import (ClientEditor, UserEditor,
                                              CardProviderEditor,
                                              EmployeeRoleEditor,
                                              EmployeeEditor, SupplierEditor,
                                              TransporterEditor, BranchEditor)
from stoqlib.gui.search.callsearch import CallsSearch
from stoqlib.gui.search.creditcheckhistorysearch import CreditCheckHistorySearch
from stoqlib.gui.uitestutils import GUITest, GUIDumper


class _BasePersonEditorTest(GUITest):
    editor = None

    @mock.patch('stoqlib.gui.templates.persontemplate.run_dialog')
    def testRunDialogParent(self, run_dialog):
        editor = self.editor(self.trans, role_type=Person.ROLE_INDIVIDUAL)
        person_slave = editor._person_slave

        buttons_dialogs = [
            (person_slave.calls_button, CallsSearch),
            (person_slave.contacts_button, LiaisonListDialog),
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
            self.assertEqual(args, (dialog, editor, editor.conn))


class TestClientEditor(_BasePersonEditorTest):
    editor = ClientEditor

    def testCreateIndividual(self):
        editor = ClientEditor(self.trans, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-client-individual-create')

    def testCreateCompany(self):
        editor = ClientEditor(self.trans, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-client-company-create')

    @mock.patch('stoqlib.gui.templates.persontemplate.warning')
    def testEditWithoutAddress(self, warning):
        client = self.create_client()
        editor = ClientEditor(self.trans, client,
                              role_type=Person.ROLE_INDIVIDUAL)
        self.click(editor.get_person_slave().address_button)

        warning.assert_called_once_with(
            'You must define a valid main address before\n'
            'adding additional addresses')

    @mock.patch('stoqlib.gui.templates.persontemplate.warning')
    def testEditAddress(self, warning):
        client = Person.selectBy(name="Franciso Elisio de Lima Junior",
                                 connection=self.trans)[0].client
        editor = ClientEditor(self.trans, client,
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


class TestUserEditor(_BasePersonEditorTest):
    editor = UserEditor

    def testCreateIndividual(self):
        editor = UserEditor(self.trans, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-user-individual-create')

    def testCreateCompany(self):
        editor = UserEditor(self.trans, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-user-company-create')


class TestCardProviderEditor(_BasePersonEditorTest):
    editor = CardProviderEditor

    def testCreateIndividual(self):
        editor = CardProviderEditor(
            self.trans, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-creditprovider-individual-create')

    def testCreateCompany(self):
        editor = CardProviderEditor(
            self.trans, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-creditprovider-company-create')


class TestEmployeeEditor(_BasePersonEditorTest):
    editor = EmployeeEditor

    def testCreateIndividual(self):
        branch = self.create_branch()
        role = self.create_employee_role()

        editor = EmployeeEditor(self.trans, role_type=Person.ROLE_INDIVIDUAL)
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

    def testCreateCompany(self):
        editor = EmployeeEditor(self.trans, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-employee-company-create')


class TestSupplierEditor(_BasePersonEditorTest):
    editor = SupplierEditor

    def testCreateIndividual(self):
        editor = SupplierEditor(self.trans, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-supplier-individual-create')

    def testCreateCompany(self):
        editor = SupplierEditor(self.trans, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-supplier-company-create')


class TestTransporterEditor(_BasePersonEditorTest):
    editor = TransporterEditor

    def testCreateIndividual(self):
        editor = TransporterEditor(
            self.trans, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(
            editor, 'editor-transporter-individual-create')

    def testCreateCompany(self):
        editor = TransporterEditor(
            self.trans, role_type=Person.ROLE_COMPANY)
        self.check_editor(
            editor, 'editor-transporter-company-create')


class TestBranchEditor(_BasePersonEditorTest):
    editor = BranchEditor

    def testCreateIndividual(self):
        editor = BranchEditor(self.trans, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-branch-individual-create')

    def testCreateCompany(self):
        editor = BranchEditor(self.trans, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-branch-company-create')


class TestEmployeeRoleEditor(GUITest):
    def testCreate(self):
        editor = EmployeeRoleEditor(self.trans)
        self.check_editor(editor, 'editor-employeerole-create')
