# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
""" Person editors definition """

import datetime

from kiwi.datatypes import ValidationError

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.simpleeditor import SimpleEntryEditor
from stoqlib.gui.templates.persontemplate import BasePersonRoleEditor
from stoqlib.gui.slaves.clientslave import ClientStatusSlave
from stoqlib.gui.slaves.credproviderslave import CreditProviderDetailsSlave
from stoqlib.gui.slaves.employeeslave import (EmployeeDetailsSlave,
                                      EmployeeStatusSlave,
                                      EmployeeRoleSlave,
                                      EmployeeRoleHistorySlave)
from stoqlib.gui.slaves.userslave import UserDetailsSlave, UserStatusSlave

from stoqlib.gui.slaves.supplierslave import SupplierDetailsSlave
from stoqlib.gui.slaves.transporterslave import TransporterDataSlave
from stoqlib.gui.slaves.branchslave import BranchDetailsSlave
from stoqlib.domain.person import EmployeeRole, PersonAdaptToCreditProvider
from stoqlib.domain.interfaces import (IClient, ICreditProvider, IEmployee,
                                       ISupplier, ITransporter, IUser,
                                       IIndividual, IBranch)

_ = stoqlib_gettext


class ClientEditor(BasePersonRoleEditor):
    model_name = _('Client')
    title = _('New Client')
    model_iface = IClient
    gladefile = 'BaseTemplate'

    help_section = 'client'
    ui_form_name = 'client'

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        client = IClient(person, None)
        if client is None:
            client = person.addFacet(IClient, connection=conn)
        return client

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        self.status_slave = ClientStatusSlave(self.conn, self.model,
                                              visual_mode=self.visual_mode)
        self.main_slave.attach_person_slave(self.status_slave)


class UserEditor(BasePersonRoleEditor):
    model_name = _('User')
    title = _('New User')
    model_iface = IUser
    gladefile = 'BaseTemplate'
    USER_TAB_POSITION = 0

    help_section = 'user'
    ui_form_name = 'user'

    def __init__(self, conn, model=None, role_type=None, person=None,
                 visual_mode=False):
        BasePersonRoleEditor.__init__(self, conn, model, role_type, person,
                                      visual_mode=visual_mode)

    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        user = IUser(person, None)
        return user or person.addFacet(IUser, connection=conn, username="",
                                       password="", profile=None)

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        user_status = UserStatusSlave(self.conn, self.model)
        self.main_slave.attach_person_slave(user_status)
        passwd_fields = not self.edit_mode
        self.user_details = UserDetailsSlave(self.conn, self.model,
            show_password_fields=passwd_fields,
            visual_mode=self.visual_mode)
        tab_text = _('User Details')
        self.main_slave._person_slave.attach_custom_slave(self.user_details,
                                                          tab_text)
        tab_child = self.main_slave._person_slave.custom_tab
        notebook = self.main_slave._person_slave.person_notebook
        notebook.reorder_child(tab_child, position=self.USER_TAB_POSITION)
        notebook.set_current_page(self.USER_TAB_POSITION)

    def validate_confirm(self):
        return self.user_details.validate_confirm()

    def on_confirm(self):
        self.main_slave.on_confirm()
        self.user_details.on_confirm()
        return self.model


class CreditProviderEditor(BasePersonRoleEditor):
    model_name = _('Credit Provider')
    title = _('New Credit Provider')
    model_iface = ICreditProvider
    gladefile = 'BaseTemplate'
    provtype = None

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        credprovider = ICreditProvider(person, None)
        if credprovider:
            return credprovider
        if self.provtype is None:
            raise ValueError('Subclasses of CreditProviderEditor must '
                             'define a provtype attribute')
        return person.addFacet(ICreditProvider, short_name='',
                               provider_type=self.provtype,
                               open_contract_date=datetime.datetime.today(),
                               connection=conn)

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        klass = CreditProviderDetailsSlave
        self.details_slave = klass(self.conn, self.model,
                                   visual_mode=self.visual_mode)
        slave = self.main_slave.get_person_slave()
        slave.attach_slave('person_status_holder', self.details_slave)


class CardProviderEditor(CreditProviderEditor):
    model_name = _('Card Provider')
    title = _('New Card Provider')
    provtype = PersonAdaptToCreditProvider.PROVIDER_CARD


class EmployeeEditor(BasePersonRoleEditor):
    model_name = _('Employee')
    title = _('New Employee')
    model_iface = IEmployee
    gladefile = 'BaseTemplate'

    ui_form_name = 'employee'

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        if not IIndividual(person, None):
            person.addFacet(IIndividual, connection=self.conn)
        employee = IEmployee(person, None)
        if not employee:
            employee = person.addFacet(IEmployee, connection=conn, role=None)
        return employee

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        if not self.individual_slave:
            raise ValueError('This editor must have an individual slave')
        self.details_slave = EmployeeDetailsSlave(self.conn, self.model,
                                                  visual_mode=self.visual_mode)
        custom_tab_label = _('Employee Data')
        slave = self.individual_slave
        slave._person_slave.attach_custom_slave(self.details_slave,
                                                custom_tab_label)
        self.status_slave = EmployeeStatusSlave(self.conn, self.model,
                                                visual_mode=self.visual_mode)
        slave.attach_person_slave(self.status_slave)
        self.role_slave = EmployeeRoleSlave(self.conn, self.model,
                                            edit_mode=self.edit_mode,
                                            visual_mode=self.visual_mode)
        db_form = self._person_slave.db_form
        slave._person_slave.attach_role_slave(self.role_slave)

        if db_form:
            db_form.update_widget(self.role_slave.role,
                                  other=self.role_slave.role_lbl)
            db_form.update_widget(self.role_slave.salary,
                                  other=self.role_slave.salary_lbl)

        history_tab_label = _("Role History")
        history_slave = EmployeeRoleHistorySlave(self.model)
        slave._person_slave.attach_extra_slave(history_slave,
                                               history_tab_label)

    def on_confirm(self):
        self.individual_slave.on_confirm()
        self.role_slave.on_confirm()
        return self.model


class EmployeeRoleEditor(SimpleEntryEditor):
    model_type = EmployeeRole
    model_name = _('Employee Role')
    size = (330, 130)

    def __init__(self, conn, model, visual_mode=False):
        SimpleEntryEditor.__init__(self, conn, model, attr_name='name',
                                   name_entry_label=_('Role Name:'),
                                   visual_mode=visual_mode)
        self.set_description(self.model.name)

    #
    # BaseEditorSlave Hooks
    #

    def create_model(self, conn):
        return EmployeeRole(connection=conn, name='')

    def on_cancel(self):
        # XXX This will prevent problems in case that you can't
        # update the connection.
        if not self.edit_mode:
            self.model_type.delete(self.model.id, connection=self.conn)

    #
    # Kiwi handlers
    #

    def on_name_entry__validate(self, widget, value):
        if self.model.has_other_role(value):
            return ValidationError('This role already exists!')


class SupplierEditor(BasePersonRoleEditor):
    model_name = _('Supplier')
    title = _('New Supplier')
    model_iface = ISupplier
    gladefile = 'BaseTemplate'

    help_section = 'supplier'
    ui_form_name = 'supplier'

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        supplier = ISupplier(person, None)
        if supplier is None:
            supplier = person.addFacet(ISupplier, connection=conn)
        return supplier

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        self.details_slave = SupplierDetailsSlave(self.conn, self.model,
                                                  visual_mode=self.visual_mode)
        slave = self.main_slave.get_person_slave()
        slave.attach_slave('person_status_holder', self.details_slave)


class TransporterEditor(BasePersonRoleEditor):
    model_name = _('Transporter')
    title = _('New Transporter')
    model_iface = ITransporter
    gladefile = 'BaseTemplate'

    help_section = 'transporter'
    ui_form_name = 'transporter'

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        transporter = ITransporter(person, None)
        if transporter is None:
            transporter = person.addFacet(ITransporter, connection=conn)
        return transporter

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        self.details_slave = TransporterDataSlave(self.conn,
                                                  self.model,
                                                  visual_mode=self.visual_mode)
        slave = self.main_slave.get_person_slave()
        slave.attach_slave('person_status_holder', self.details_slave)


class BranchEditor(BasePersonRoleEditor):
    model_name = _('Branch')
    title = _('New Branch')
    model_iface = IBranch
    gladefile = 'BaseTemplate'

    help_section = 'branch'
    ui_form_name = 'branch'

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        branch = IBranch(person, None)
        if branch is None:
            branch = person.addFacet(IBranch, connection=conn)

        return branch

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        self.status_slave = BranchDetailsSlave(self.conn, self.model,
                                               visual_mode=self.visual_mode)
        self.main_slave.attach_person_slave(self.status_slave)
