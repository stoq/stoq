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
## Author(s): Henrique Romano             <henrique@async.com.br>
##            Evandro Vale Miquelito      <evandro@async.com.br>
##            Ariqueli Tejada Fonseca     <aritf@async.com.br>
##            Bruno Rafael Garcia         <brg@async.com.br>
##
"""
stoq/gui/editors/person.py

    Person editors definition
"""

import datetime

import gtk
import gettext
from sqlobject.sqlbuilder import func
from kiwi.datatypes import ValidationError
from stoqlib.gui.editors import SimpleEntryEditor, BaseEditor

from stoq.lib.runtime import new_transaction
from stoq.gui.templates.person import BasePersonRoleEditor
from stoq.gui.slaves.client import ClientStatusSlave
from stoq.gui.slaves.credprovider import CreditProviderDetailsSlave
from stoq.gui.slaves.employee import (EmployeeDetailsSlave,
                                      EmployeeStatusSlave)
from stoq.gui.slaves.user import (UserDetailsSlave, UserStatusSlave,
                                  PasswordEditorSlave)
from stoq.gui.slaves.supplier import SupplierDetailsSlave
from stoq.gui.slaves.transporter import TransporterDataSlave
from stoq.domain.person import Person, EmployeeRole, LoginInfo
from stoq.domain.interfaces import (IClient, ICreditProvider, IEmployee,
                                    ISupplier, ITransporter, IUser)

_ = gettext.gettext


class ClientEditor(BasePersonRoleEditor):
    model_name = _('Client')
    model_type = Person.getAdapterClass(IClient)
    gladefile = 'BaseTemplate'
    widgets = ('main_holder', )

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        client = IClient(person, connection=conn)
        return client or person.addFacet(IClient, connection=conn)

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        self.status_slave = ClientStatusSlave(self.conn, self.model)
        self.main_slave.attach_person_slave(self.status_slave)

        
class UserEditor(BasePersonRoleEditor):
    model_name = _('User')
    model_type = Person.getAdapterClass(IUser)
    gladefile = 'BaseTemplate'
    widgets = ('main_holder',)
    USER_TAB_POSITION = 0

    #
    # BaseEditorSlaves Hooks
    #

    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        user = IUser(person, connection=conn)
        return user or person.addFacet(IUser, connection=conn, username="", 
                                       password="", profile=None)

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self) 
        user_status = UserStatusSlave(self.conn, self.model)
        self.main_slave.attach_person_slave(user_status) 
        passwd_fields = not self.edit_mode
        klass = UserDetailsSlave
        self.user_details = klass(self.conn, self.model,
                                  show_password_fields=passwd_fields)
        tab_text = _('User Details')
        self.main_slave._person_slave.attach_custom_slave(self.user_details,
                                                          tab_text)
        tab_child = self.main_slave._person_slave.custom_tab
        notebook = self.main_slave._person_slave.person_notebook
        notebook.reorder_child(tab_child, position=self.USER_TAB_POSITION)
        notebook.set_current_page(self.USER_TAB_POSITION)

    def on_confirm(self):
        self.main_slave.on_confirm()
        self.user_details.on_confirm()
        return self.model
        

class PasswordEditor(BaseEditor):
    gladefile = 'PasswordEditor'
    model_type = LoginInfo
    proxy_widgets = ('current_password',)
    size_group_widgets = ('current_password_lbl',)

    def __init__(self, conn, user):
        self.user = user
        BaseEditor.__init__(self, conn)
        self._setup_widgets()

    def _setup_size_group(self, size_group, widgets, obj):
        for widget_name in widgets:
            widget = getattr(obj, widget_name)
            size_group.add_widget(widget)        

    def _setup_widgets(self):
        self.password_slave.set_password_labels(_('New Password:'), 
                                                _('Retype New Password:'))
        size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self._setup_size_group(size_group,
                               PasswordEditor.size_group_widgets,
                               self)
        self._setup_size_group(size_group,
                               self.password_slave.size_group_widgets,
                               self.password_slave)

    #
    # BaseEditorSlave Hooks
    #

    def get_title(self, model):
        title = _('Change "%s" Password' % self.user.username)
        return title

    def create_model(self, conn):
        return LoginInfo()

    def setup_slaves(self):
        self.password_slave = PasswordEditorSlave(self.conn, self.model)
        self.attach_slave('password_holder', self.password_slave)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    PasswordEditor.proxy_widgets)

    def on_confirm(self):
        self.user.password = self.model.new_password
        return self.user

    def on_current_password__validate(self, widget, value):
        if value != self.user.password:
            return ValidationError(_('Wrong password'))


class CreditProviderEditor(BasePersonRoleEditor):
    model_name = _('Credit Provider')
    model_type = Person.getAdapterClass(ICreditProvider)
    gladefile = 'BaseTemplate'
    widgets = ('main_holder', )

    #
    # BaseEditor hooks
    #
    
    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        credprovider = ICreditProvider(person, connection=conn)
        if credprovider:
            return credprovider
        return person.addFacet(ICreditProvider, short_name='',
                               open_contract_date=datetime.datetime.today(),
                               connection=conn)

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        self.details_slave = CreditProviderDetailsSlave(self.conn, 
                                                        self.model)
        slave = self.main_slave.get_person_slave()
        slave.attach_slave('person_status_holder', self.details_slave)


class EmployeeEditor(BasePersonRoleEditor):
    model_name = _('Employee')
    model_type = Person.getAdapterClass(IEmployee)
    gladefile = 'BaseTemplate'
    widgets = ('main_holder', )

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        employee = IEmployee(person, connection=conn)
        return employee or person.addFacet(IEmployee, connection=conn,
                                           role=None)

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        if not self.individual_slave:
            raise ValueError('This editor must have an individual slave')
        self.details_slave = EmployeeDetailsSlave(self.conn, self.model)
        tab_text = _('Employee Data')
        slave = self.individual_slave
        slave._person_slave.attach_custom_slave(self.details_slave,
                                                tab_text)
        self.status_slave = EmployeeStatusSlave(self.conn, self.model)
        slave.attach_person_slave(self.status_slave)


class EmployeeRoleEditor(SimpleEntryEditor):
    model_type = EmployeeRole
    model_name = _('Employee Role')
    size = (330, 130)
  
    def __init__(self, conn, model):
        SimpleEntryEditor.__init__(self, conn, model, attr_name='name',
                                   name_entry_label='Role Name:')
        self.main_dialog.enable_notices()

    #
    # BaseEditor Hooks
    #

    def get_title_model_attribute(self, model):
        return model.name

    # 
    # BaseEditorSlave Hooks 
    #
    
    def create_model(self, conn):
        return EmployeeRole(connection=conn, name='')

    #     
    # BasicPluggableDialog Hooks
    #         

    def after_name_entry__changed(self, *args):
        self.main_dialog.clear_notices()
        role_name = self.name_entry.get_text()
        conn = new_transaction() 
        self.main_dialog.enable_ok()
        for role in EmployeeRole.select(connection=conn):
            query = func.UPPER(EmployeeRole.q.name) == role_name.upper()
            if EmployeeRole.select(query, connection=conn).count():       
                msg = _('This role already exists!')
                # FIXME enable this line after a bug fix in kiwi
                # self.name_entry.set_invalid(msg)
                self.main_dialog.disable_ok()
                # XXX We will not need this line when kiwi provide 
                # support for validation when changing the model 
                # attribute dynamically
                self.main_dialog.alert(msg)
                return False
        self.model.name = role_name
        return self.model


class SupplierEditor(BasePersonRoleEditor):
    model_name = _('Supplier')
    model_type = Person.getAdapterClass(ISupplier)
    gladefile = 'BaseTemplate'
    widgets = ('main_holder', )

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        supplier = ISupplier(person, connection=conn)
        return supplier or person.addFacet(ISupplier, connection=conn)

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        self.details_slave = SupplierDetailsSlave(self.conn, self.model)
        slave = self.main_slave.get_person_slave()
        slave.attach_slave('person_status_holder', self.details_slave)


class TransporterEditor(BasePersonRoleEditor):
    model_name = _('Transporter')
    model_type = Person.getAdapterClass(ITransporter)
    gladefile = 'BaseTemplate'
    widgets = ('main_holder', )

    #
    # BaseEditor hooks
    #
    
    def create_model(self, conn):
        person = BasePersonRoleEditor.create_model(self, conn)
        transporter = ITransporter(person, connection=conn)
        if transporter:
            return transporter
        return person.addFacet(ITransporter, connection=conn)

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        self.details_slave = TransporterDataSlave(self.conn, 
                                                  self.model)
        slave = self.main_slave.get_person_slave()
        slave.attach_slave('person_status_holder', self.details_slave)
