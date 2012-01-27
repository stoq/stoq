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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Person role wizards definition """

from kiwi.python import Settable
from kiwi.argcheck import argcheck
from kiwi.ui.widgets.list import Column

from stoqlib.api import api
from stoqlib.database.orm import Transaction, OR, LIKE
from stoqlib.domain.person import Person
from stoqlib.gui.base.wizards import (WizardEditorStep, BaseWizard,
                                      BaseWizardStep)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.personeditor import BranchEditor, UserEditor
from stoqlib.gui.templates.persontemplate import BasePersonRoleEditor
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_phone_number, raw_phone_number


_ = stoqlib_gettext

#
# Wizard Steps
#


class RoleEditorStep(BaseWizardStep):
    gladefile = 'HolderTemplate'

    def __init__(self, wizard, conn, previous, role_type, person=None,
                 phone_number=None):
        BaseWizardStep.__init__(self, conn, wizard, previous=previous)
        role_editor = self.wizard.role_editor(self.conn,
                                              person=person,
                                              role_type=role_type)
        self.wizard.set_editor(role_editor)
        if phone_number is not None:
            role_editor.set_phone_number(phone_number)
        self.person_slave = role_editor.get_person_slave()
        self.person_slave.get_toplevel().reparent(self.place_holder)

    def post_init(self):
        refresh_method = self.wizard.refresh_next
        self.person_slave.register_validate_function(refresh_method)
        self.person_slave.force_validation()

    def previous_step(self):
        # We don't want to create duplicate person objects when switching
        # steps.
        api.rollback_and_begin(self.conn)
        return BaseWizardStep.previous_step(self)

    def has_next_step(self):
        return False


class ExistingPersonStep(BaseWizardStep):
    gladefile = 'ExistingPersonStep'

    def __init__(self, wizard, conn, previous, role_type, person_list,
                 phone_number=''):
        self.phone_number = phone_number
        self.role_type = role_type
        BaseWizardStep.__init__(self, conn, wizard, previous=previous)
        self._setup_widgets(person_list)

    def _setup_widgets(self, person_list):
        role_name = self.wizard.get_role_name().lower()
        self.question_label.set_text(
            _("Does the %s already exist?") % role_name)
        self.existing_person_check.set_label(_("Yes"))
        self.new_person_check.set_label(
            _("No, it's a new %s") % role_name)
        self.question_label.set_size('large')
        self.question_label.set_bold(True)
        self.person_list.set_columns(self._get_columns())
        self.person_list.add_list(person_list)
        self.person_list.select(person_list[0])

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
            phone_number = None
        else:
            person = None
            phone_number = self.phone_number
        return RoleEditorStep(self.wizard, self.conn, self,
                              self.role_type, person, phone_number)


class PersonRoleTypeStep(WizardEditorStep):
    gladefile = 'PersonRoleTypeStep'
    model_type = Settable

    def __init__(self, wizard, conn):
        WizardEditorStep.__init__(self, conn, wizard)
        self._setup_widgets()

    def _setup_widgets(self):
        label = _('What kind of %s are you adding?')
        role_editor = self.wizard.role_editor
        if role_editor == BranchEditor or role_editor == UserEditor:
            self.company_check.set_sensitive(False)
            self.individual_check.set_sensitive(False)
            if role_editor == UserEditor:
                self.individual_check.set_active(True)
            else:
                label = _('Adding a %s')
                self.company_check.set_active(True)
        role_name = self.wizard.get_role_name().lower()
        self.person_role_label.set_text(label % role_name)
        self.person_role_label.set_size('large')
        self.person_role_label.set_bold(True)

    #
    # WizardStep hooks
    #

    def create_model(self, conn):
        return Settable(phone_number=u'')

    def setup_proxies(self):
        self.add_proxy(self.model, ['phone_number'])

    def next_step(self):
        phone_number = self.model.phone_number
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
        if persons:
            return ExistingPersonStep(self.wizard, self.conn, self,
                                      role_type, persons,
                                      phone_number=phone_number)
        return RoleEditorStep(self.wizard, self.conn, self, role_type,
                              phone_number=phone_number)

    def has_previous_step(self):
        return False

    # Callbacks

    def on_phone_number__activate(self, entry):
        self.wizard.go_to_next()


#
# Main wizard
#


class PersonRoleWizard(BaseWizard):

    size = (650, 450)

    def __init__(self, conn, role_editor):
        if not issubclass(role_editor, BasePersonRoleEditor):
            raise TypeError('Editor %s must be BasePersonRoleEditor '
                            'instance' % role_editor)
        self.role_editor = role_editor

        BaseWizard.__init__(self, conn,
                            PersonRoleTypeStep(self, conn),
                            title=self.get_role_title())

        if role_editor.help_section:
            self.set_help_section(role_editor.help_section)

    def get_role_name(self):
        if not self.role_editor.model_name:
            raise ValueError('Editor %s must define a model_name attribute '
                             % self.role_editor)
        return self.role_editor.model_name

    def get_role_title(self):
        if not self.role_editor.title:
            raise ValueError('Editor %s must define a title attribute '
                             % self.role_editor)
        return self.role_editor.title

    def set_editor(self, editor):
        self.editor = editor

    #
    # WizardStep hooks
    #

    def finish(self):
        if not self.editor.validate_confirm():
            return
        self.editor.on_confirm()
        self.retval = self.editor.model
        self.close()


argcheck(BasePersonRoleEditor, object, Transaction, object)


def run_person_role_dialog(role_editor, parent, conn, model=None,
                           **editor_kwargs):
    if not model:
        return run_dialog(PersonRoleWizard, parent, conn, role_editor,
                          **editor_kwargs)
    return run_dialog(role_editor, parent, conn, model, **editor_kwargs)
