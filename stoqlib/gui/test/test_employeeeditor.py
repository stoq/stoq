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


from decimal import Decimal

from stoqlib.domain.person import Person
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.editors.personeditor import EmployeeEditor


class TestEmployeeEditor(GUITest):
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
        employee_role_slave.salary.update(Decimal('50'))

        details_slave = editor.details_slave
        details_slave.branch_combo.update(branch)

        self.click(editor.main_dialog.ok_button)
        self.check_editor(editor, 'editor-employee-individual-create-confirmed',
                          [editor.retval, branch])

    def testCreateCompany(self):
        editor = EmployeeEditor(self.trans, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-employee-company-create')
