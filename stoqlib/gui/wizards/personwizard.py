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
from kiwi.datatypes import ValidationError

from stoqlib.api import api
from stoqlib.domain.person import Person
from stoqlib.gui.base.wizards import (WizardEditorStep, BaseWizard,
                                      BaseWizardStep)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.personeditor import BranchEditor, UserEditor
from stoqlib.gui.templates.persontemplate import BasePersonRoleEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

#
# Wizard Steps
#


class RoleEditorStep(BaseWizardStep):
    gladefile = 'HolderTemplate'

    def __init__(self, wizard, store, previous, role_type, person=None,
                 document=None, description=None):
        BaseWizardStep.__init__(self, store, wizard, previous=previous)
        self.role_editor = self.wizard.role_editor(self.store,
                                                   person=person,
                                                   role_type=role_type,
                                                   parent=self.wizard,
                                                   document=document,
                                                   description=description)

        self.wizard.set_editor(self.role_editor)
        self.person_slave = self.role_editor.get_person_slave()
        self.person_slave.get_toplevel().reparent(self.place_holder)

    def post_init(self):
        refresh_method = self.wizard.refresh_next
        self.person_slave.register_validate_function(refresh_method)
        self.person_slave.force_validation()

    def previous_step(self):
        # We don't want to create duplicate person objects when switching
        # steps.
        self.store.rollback(close=False)
        return BaseWizardStep.previous_step(self)

    def has_next_step(self):
        return False


class PersonRoleTypeStep(WizardEditorStep):
    gladefile = 'PersonRoleTypeStep'
    model_type = Settable

    def __init__(self, wizard, store, document=None, description=None):
        self._description = description
        self._document = document
        WizardEditorStep.__init__(self, store, wizard)
        self._setup_widgets()

    def _setup_widgets(self):
        self.document_l10n = api.get_l10n_field('person_document')
        self.person_document.set_mask(self.document_l10n.entry_mask)
        self.person_document.set_width_chars(17)
        if self._document:
            self.person_document.update(self._document)

        self.document_label.set_text(self.document_l10n.label)
        # Just adding some labels
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

        self.register_validate_function(self.wizard.refresh_next)

    #
    # WizardStep hooks
    #

    def create_model(self, store):
        return Settable(document=u'')

    def setup_proxies(self):
        self.add_proxy(self.model, ['person_document'])

    def next_step(self):
        if self.individual_check.get_active():
            role_type = Person.ROLE_INDIVIDUAL
        else:
            role_type = Person.ROLE_COMPANY

        # If someone wants to register with an empty document
        if self.person_document.is_empty():
            return RoleEditorStep(self.wizard, self.store, self, role_type,
                                  description=self._description)

        person = Person.get_by_document(self.store, self.model.person_document)
        return RoleEditorStep(self.wizard, self.store, self, role_type, person,
                              document=self.model.person_document)

    def has_previous_step(self):
        return False

    # Callbacks

    def on_person_document__activate(self, entry):
        self.wizard.go_to_next()

    def on_person_document__validate(self, entry, value):
        # FIXME: There is a bug in kiwi that this method gets called when
        # setting the mask.
        if not self.person_document.mask:
            return

        # This will allow the user to use an empty value to this field
        if self.person_document.is_empty():
            return

        if not self.document_l10n.validate(value):
            return ValidationError(_('%s is not valid.') %
                                   (self.document_l10n.label,))

    def on_individual_check__toggled(self, *args):
        """
        Change document labels based on check button

        Changes the document_label (proxy_widget) with the right document (CPF or CNPJ)
        that will be inserted on the person_document entry. Also changes the mask of
        person_document when is necessary
        """
        if self.individual_check.get_active():
            self.document_l10n = api.get_l10n_field('person_document')
            self.document_label.set_text(self.document_l10n.label + ':')
            # Change the entry size (in chars) to accomodate the cpf
            self.person_document.set_width_chars(17)
        else:
            self.document_l10n = api.get_l10n_field('company_document')
            self.document_label.set_text(self.document_l10n.label + ':')
            # Change the entry size (in chars) to accomodate the cnpj
            self.person_document.set_width_chars(21)

        self.person_document.set_mask(self.document_l10n.entry_mask)


#
# Main wizard
#


class PersonRoleWizard(BaseWizard):

    size = (650, 450)

    def __init__(self, store, role_editor, document=None, description=None):
        if not issubclass(role_editor, BasePersonRoleEditor):
            raise TypeError('Editor %s must be BasePersonRoleEditor '
                            'instance' % role_editor)
        self.role_editor = role_editor
        self._description = description
        self._document = document

        BaseWizard.__init__(self, store,
                            self.get_first_step(store),
                            title=self.get_role_title())

        if role_editor.help_section:
            self.set_help_section(role_editor.help_section)

    def get_first_step(self, store):
        return PersonRoleTypeStep(self, store,
                                  document=self._document,
                                  description=self._description)

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
        if not self.editor.confirm():
            return
        self.retval = self.editor.model
        self.close()


def run_person_role_dialog(role_editor, parent, store, model=None,
                           **editor_kwargs):
    if not model:
        editor_kwargs.pop('visual_mode', None)
        return run_dialog(PersonRoleWizard, parent, store, role_editor,
                          **editor_kwargs)
    return run_dialog(role_editor, parent, store, model, **editor_kwargs)
