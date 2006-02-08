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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/wizards/person.py:

    Person role wizards definition
"""

import gettext

from sqlobject.dbconnection import Transaction
from sqlobject.sqlbuilder import OR, LIKE
from kiwi.datatypes import ValidationError
from kiwi.argcheck import argcheck
from kiwi.ui.widgets.list import Column
from stoqlib.gui.base.wizards import BaseWizardStep, BaseWizard
from stoqlib.gui.base.dialogs import run_dialog

from stoqlib.domain.person import Person
from stoq.gui.templates.person import BasePersonRoleEditor
from stoqlib.gui.editors.person import (BranchEditor,
                                        ClientEditor, SupplierEditor,
                                        EmployeeEditor, 
                                        CreditProviderEditor)
from stoqlib.lib.validators import (validate_phone_number, format_phone_number,
                                    raw_phone_number)


_ = gettext.gettext

#
# Wizard Steps
#

class RoleEditorStep(BaseWizardStep):
    gladefile = 'HolderTemplate'
    model_type = None

    def __init__(self, wizard, conn, previous, role_type, person=None):
        BaseWizardStep.__init__(self, conn, wizard, previous=previous)
        role_editor = self.wizard.role_editor(self.conn, 
                                              person=person,
                                              role_type=role_type)
        self.wizard.set_editor(role_editor)
        self.person_slave = role_editor.get_person_slave()
        self.person_slave.get_toplevel().reparent(self.place_holder)

    def post_init(self):
        refresh_method = self.wizard.refresh_next
        self.person_slave.register_validate_function(refresh_method)
        self.person_slave.force_validation()

    def has_next_step(self):
        return False


class ExistingPersonStep(BaseWizardStep):
    gladefile = 'ExistingPersonStep'
    model_type = None

    def __init__(self, wizard, conn, previous, role_type, person_list):
        self.role_type = role_type
        BaseWizardStep.__init__(self, conn, wizard, previous=previous)
        self._setup_widgets(person_list)

    def _setup_widgets(self, person_list):
        role_name = self.wizard.get_role_name().lower()
        label = _("Does the %s already exists?") % role_name
        self.question_label.set_text(label)
        label = _("Yes")
        self.existing_person_check.set_label(label)
        label = _("No, it's a new %s") % role_name
        self.new_person_check.set_label(label)
        self.question_label.set_size('large')
        self.question_label.set_bold(True)
        self.person_list.set_columns(self._get_columns())
        self.person_list.add_list(person_list)

    def _get_columns(self):
        return [Column('name', title=_('Name'), sorted=True, 
                       data_type=str, width=220),
                Column('phone_number', title=_('Phone Number'), 
                       data_type=str, width=120,
                       format_func=format_phone_number),
                Column('mobile_number', title=_('Mobile'), data_type=str,
                       format_func=format_phone_number,
                       width=120)]

    def on_existing_person_check__toggled(self, *args):
        self.person_list.set_sensitive(True)

    def on_new_person_check__toggled(self, *args):
        self.person_list.set_sensitive(False)

    def next_step(self):
        if self.existing_person_check.get_active():
            person = self.person_list.get_selected()
        else:
            person = None
        return RoleEditorStep(self.wizard, self.conn, self, 
                              self.role_type, person)


class PersonRoleTypeStep(BaseWizardStep):
    gladefile = 'PersonRoleTypeStep'
    model_type = None

    def __init__(self, wizard, conn):
        BaseWizardStep.__init__(self, conn, wizard)
        self._setup_widgets()

    def _setup_widgets(self):
        if self.wizard.role_editor == BranchEditor:
            label = _('Adding a new %s')
            self.individual_check.set_sensitive(False)
            self.company_check.set_sensitive(False)
            self.company_check.set_active(True)
        else:
            label = _('What kind of %s are you adding?')
        role_name = self.wizard.get_role_name().lower()
        self.person_role_label.set_text(label % role_name)
        self.person_role_label.set_size('large')
        self.person_role_label.set_bold(True)

    def on_phone_number__validate(self, entry, phone_number):
        if not validate_phone_number(phone_number):
            # XXX Improve this error message
            return ValidationError("Invalid Phone Number")

    #
    # WizardStep hooks
    #

    def next_step(self):
        phone_number = self.phone_number.get_text()
        if phone_number:
            phone_number = '%%%s%%' % raw_phone_number(phone_number)
            query = OR(LIKE(Person.q.phone_number, phone_number),
                       LIKE(Person.q.mobile_number, phone_number))
            persons = Person.select(query, connection=self.conn)
        else:
            persons = None
        if self.individual_check.get_active():
            role_type = Person.ROLE_INDIVIDUAL
        else:
            role_type = Person.ROLE_COMPANY
        step_args = [self.wizard, self.conn, self, role_type]
        if persons and persons.count():
            step_args.append(persons)
            return ExistingPersonStep(*step_args)
        return RoleEditorStep(*step_args)

    def has_previous_step(self):
        return False


#
# Main wizard
#


class PersonRoleWizard(BaseWizard):

    ROLE_CLIENT = ClientEditor
    ROLE_SUPPLIER = SupplierEditor
    ROLE_CREDPROVIDER = CreditProviderEditor
    ROLE_EMPLOYEE = EmployeeEditor

    size = (650, 450)
    
    def __init__(self, conn, role_editor):
        if not issubclass(role_editor, BasePersonRoleEditor):
            raise TypeError('Editor %s must be BasePersonRoleEditor '
                            'instance' % role_editor)
        self.role_editor = role_editor
        
        BaseWizard.__init__(self, conn, 
                            PersonRoleTypeStep(self, conn),
                            title=_('New %s') % self.get_role_name())

    def get_role_name(self):
        if not self.role_editor.model_name:
            raise ValueError('Editor %s must define a model_name attribute '
                             % self.role_editor)
        return self.role_editor.model_name

    def set_editor(self, editor):
        self.editor = editor

    #
    # WizardStep hooks
    #

    def finish(self):
        self.editor.on_confirm()
        self.retval = self.editor.model
        self.close()


argcheck(BasePersonRoleEditor, object, Transaction, object)
def run_person_role_dialog(role_editor, parent, conn, model=None):
    if not model:
        model = role_editor
        role_editor = PersonRoleWizard
    return run_dialog(role_editor, parent, conn, model)
