# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
""" Templates implementation for person editors.  """

from stoqlib.api import api
from stoqlib.domain.interfaces import IIndividual, ICompany
from stoqlib.domain.person import Person, PersonAdaptToSupplier
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.slaves import NoteSlave
from stoqlib.gui.databaseform import DatabaseForm
from stoqlib.gui.editors.addresseditor import (AddressAdditionDialog,
                                               AddressSlave)
from stoqlib.gui.editors.baseeditor import BaseEditorSlave, BaseEditor
from stoqlib.gui.search.callsearch import CallsSearch
from stoqlib.gui.slaves.liaisonslave import LiaisonListDialog
from stoqlib.gui.templates.companytemplate import CompanyEditorTemplate
from stoqlib.gui.templates.individualtemplate import IndividualEditorTemplate
from stoqlib.lib.message import warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _PersonEditorTemplate(BaseEditorSlave):
    model_type = Person
    gladefile = 'PersonEditorTemplate'

    proxy_widgets = ('name',
                     'phone_number',
                     'fax_number',
                     'mobile_number',
                     'email')

    def __init__(self, conn, model, visual_mode, parent):
        self._parent = parent
        if self._parent.ui_form_name:
            self.db_form = DatabaseForm(conn, self._parent.ui_form_name)
        else:
            self.db_form = None
        super(self.__class__, self).__init__(conn, model,
                                             visual_mode=visual_mode)
        self._check_new_person()

    def _check_new_person(self):
        self.is_new_person = False
        # If this person is not in the default connection, then it was created
        # inside another transaction that was not commited yet.
        if not Person.selectBy(id=self.model.id, connection=api.get_connection()):
            self.is_new_person = True

    #
    # BaseEditorSlave hooks
    #

    def create_model(self, conn):
        return Person(name="", connection=conn)

    def setup_proxies(self):
        self._setup_widgets()
        self._setup_form_fields()
        self.proxy = self.add_proxy(self.model,
                                    _PersonEditorTemplate.proxy_widgets)

    def setup_slaves(self):
        self.address_slave = AddressSlave(
            self.conn, self.model, self.model.get_main_address(),
            visual_mode=self.visual_mode,
            db_form=self.db_form)
        self.attach_slave('address_holder', self.address_slave)
        self.attach_model_slave('note_holder', NoteSlave, self.model)

    def on_confirm(self):
        self.address_slave.confirm()
        main_address = self.address_slave.model
        main_address.person = self.model
        return self.model

    #
    # Public API
    #

    def set_phone_number(self, phone_number):
        self.model.phone_number = phone_number
        self.proxy.update('phone_number')

    def attach_custom_slave(self, slave, tab_label):
        self.custom_tab.show()
        tab_child = self.custom_tab
        self.person_notebook.set_tab_label_text(tab_child, tab_label)
        self.attach_slave('custom_holder', slave)

    def attach_role_slave(self, slave):
        self.attach_slave('role_holder', slave)

    def attach_extra_slave(self, slave, tab_label):
        self.extra_tab.show()
        tab_child = self.extra_tab
        self.person_notebook.set_tab_label_text(tab_child, tab_label)
        self.attach_slave('extra_holder', slave)

    def attach_model_slave(self, name, slave_type, slave_model):
        slave = slave_type(self.conn, slave_model,
                           visual_mode=self.visual_mode)
        self.attach_slave(name, slave)
        return slave

    #
    # Kiwi handlers
    #

    def on_name__map(self, entry):
        self.name.grab_focus()

    def on_address_button__clicked(self, button):
        main_address = self.model.get_main_address()
        if not main_address.is_valid_model():
            msg = _(u"You must define a valid main address before\n"
                    "adding additional addresses")
            warning(msg)
            return

        result = run_dialog(AddressAdditionDialog, self._parent,
                            self.conn, person=self.model,
                            reuse_transaction=self.is_new_person)
        if not result:
            return

        new_main_address = self.model.get_main_address()
        if new_main_address is not main_address:
            self.address_slave.set_model(new_main_address)

    def on_contacts_button__clicked(self, button):
        run_dialog(LiaisonListDialog, self._parent, self.conn,
                   person=self.model, reuse_transaction=self.is_new_person)

    def on_calls_button__clicked(self, button):
        run_dialog(CallsSearch, self._parent, self.conn,
                   person=self.model, reuse_transaction=self.is_new_person)

    #
    # Private API
    #

    def _setup_widgets(self):
        facet_individual = IIndividual(self.model, None)
        facet_company = ICompany(self.model, None)
        if not (facet_individual or facet_company):
            raise DatabaseInconsistency('A person must have at least a '
                                        'company or an individual facet.')
        tab_child = self.person_data_tab
        if facet_individual and facet_company:
            tab_text = _('Individual/Company Data')
            self.company_frame.set_label(_('Company Data'))
            self.company_frame.show()
            self.individual_frame.set_label(_('Individual Data'))
            self.individual_frame.show()
        elif facet_individual:
            tab_text = _('Individual Data')
            self.company_frame.hide()
            self.individual_frame.set_label('')
            self.individual_frame.show()
        else:
            tab_text = _('Company Data')
            self.individual_frame.hide()
            self.company_frame.set_label('')
            self.company_frame.show()
        self.person_notebook.set_tab_label_text(tab_child, tab_text)
        addresses = self.model.get_total_addresses()
        if addresses == 2:
            self.address_button.set_label(_("1 More Address..."))
        elif addresses > 2:
            self.address_button.set_label(_("%i More Addresses...")
                                            % (addresses - 1))

    def _setup_form_fields(self):
        if not self.db_form:
            return
        self.db_form.update_widget(self.name,
                                   other=self.name_lbl)
        self.db_form.update_widget(self.phone_number,
                                   other=self.phone_number_lbl)
        self.db_form.update_widget(self.fax_number, 'fax',
                                   other=self.fax_lbl)
        self.db_form.update_widget(self.email,
                                   other=self.email_lbl)
        self.db_form.update_widget(self.mobile_number,
                                   other=self.mobile_lbl)


class BasePersonRoleEditor(BaseEditor):
    """A base class for person role editors. This class can not be
    instantiated directly.

    @ivar main_slave:
    @ivar individual_slave:
    @ivar company_slave:
    @cvar help_section: the help button for this wizard,
      usually describing how to create a new person
    """
    size = (700, -1)
    help_section = None
    ui_form_name = None

    def __init__(self, conn, model=None, role_type=None, person=None,
                 visual_mode=False):
        """ Creates a new BasePersonRoleEditor object

        @param conn: a database connection
        @param model:
        @param none_type: None, ROLE_INDIVIDUAL or ROLE_COMPANY
        @param person:
        @param visual_mode:
        """
        if not (model or role_type is not None):
            raise ValueError('A role_type attribute is required')
        self.individual_slave = None
        self.company_slave = None
        self._person_slave = None
        self.main_slave = None
        self.role_type = role_type
        self.person = person

        BaseEditor.__init__(self, conn, model, visual_mode=visual_mode)
        # FIXME: Implement and use IDescribable on the model
        self.set_description(self.model.person.name)

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        # XXX: Waiting fix for bug 2163. We should not need anymore to
        # provide empty values for mandatory attributes
        if not self.person:
            self.person = Person(name="", connection=conn)
        if not self.role_type in [Person.ROLE_INDIVIDUAL,
                                  Person.ROLE_COMPANY]:
            raise ValueError("Invalid value for role_type attribute, %r" % (
                self.role_type, ))
        if (self.role_type == Person.ROLE_INDIVIDUAL and
            not IIndividual(self.person, None)):
            self.person.addFacet(IIndividual, connection=conn)
        elif (self.role_type == Person.ROLE_COMPANY and
              not ICompany(self.person, None)):
            self.person.addFacet(ICompany, connection=conn)
        else:
            pass
        return self.person

    def setup_slaves(self):
        individual = IIndividual(self.model.person, None)
        company = ICompany(self.model.person, None)
        assert individual or company

        self._person_slave = _PersonEditorTemplate(self.conn,
                                                   self.model.person,
                                                   visual_mode=self.visual_mode,
                                                   parent=self)

        if individual:
            slave = IndividualEditorTemplate(self.conn,
                                             model=individual,
                                             person_slave=self._person_slave,
                                             visual_mode=self.visual_mode)
            self.individual_slave = slave
            self.main_slave = slave

        if company:
            slave = CompanyEditorTemplate(self.conn,
                                          model=company,
                                          person_slave=self._person_slave,
                                          visual_mode=self.visual_mode)
            self.company_slave = slave
            self.main_slave = slave

        self.attach_slave('main_holder', slave)
        self.main_slave.attach_slave('main_holder', self._person_slave)

    def on_confirm(self):
        if self.individual_slave and self.company_slave:
            self.individual_slave.on_confirm()
            self.company_slave.on_confirm(confirm_person=False)
        elif self.individual_slave:
            self.individual_slave.on_confirm()
        else:
            self.company_slave.on_confirm()
        if (isinstance(self.model, PersonAdaptToSupplier) and
                not sysparam(self.conn).SUGGESTED_SUPPLIER):
            sysparam(self.conn).SUGGESTED_SUPPLIER = self.model.id
        return self.model

    #
    # Public API
    #

    def get_person_slave(self):
        return self._person_slave

    def set_phone_number(self, phone_number):
        slave = self.get_person_slave()
        slave.set_phone_number(phone_number)
