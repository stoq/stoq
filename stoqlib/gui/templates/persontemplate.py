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
## Author(s):   Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Templates implementation for person editors.  """


from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import warning
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.domain.interfaces import IIndividual, ICompany
from stoqlib.domain.person import Person
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.editors import BaseEditorSlave, BaseEditor
from stoqlib.gui.base.slaves import NoteSlave
from stoqlib.gui.editors.addresseditor import AddressAdditionDialog
from stoqlib.gui.slaves.liaisonslave import LiaisonListDialog
from stoqlib.gui.slaves.addressslave import AddressSlave
from stoqlib.gui.slaves.companyslave import CompanyDocumentsSlave
from stoqlib.gui.slaves.individualslave import (IndividualDetailsSlave,
                                           IndividualDocuments)

_ = stoqlib_gettext


class _PersonEditorTemplate(BaseEditorSlave):
    model_type = Person
    gladefile = 'PersonEditorTemplate'

    proxy_widgets = ('name',
                     'phone_number',
                     'fax_number',
                     'mobile_number',
                     'email')

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

    #
    # Kiwi handlers
    #

    def on_address_button__clicked(self, *args):
        main_address = self.model.get_main_address()
        if not main_address.is_valid_model():
            msg = _(u"You must define a valid main address before\n"
                    "adding additional addresses")
            warning(msg)
            return
        addresses = self.model.addresses

        if addresses and main_address:
            addresses.remove(main_address)

        result = run_dialog(AddressAdditionDialog, self, self.conn,
                            addresses, person=self.model,
                            visual_mode=self.visual_mode)
        if not result:
            return

        new_main_address = self.model.get_main_address()
        if new_main_address is not main_address:
            self.address_slave.set_model(new_main_address)

    def on_contacts_button__clicked(self, *args):
        run_dialog(LiaisonListDialog, self, self.conn, self.model,
                   self.model.liaisons, visual_mode=self.visual_mode)

    #
    # BaseEditorSlave hooks
    #

    def create_model(self, conn):
        return Person(name="", connection=conn)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    _PersonEditorTemplate.proxy_widgets)

    def setup_slaves(self):
        main_address = self.model.get_main_address()
        self.address_slave = AddressSlave(self.conn, self.model,
                                          main_address,
                                          visual_mode=self.visual_mode)
        self.attach_slave('address_holder', self.address_slave)
        self.attach_model_slave('note_holder', NoteSlave, self.model)

    def on_confirm(self):
        self.address_slave.on_confirm()
        main_address = self.address_slave.model
        main_address.person = self.model
        return self.model


class _IndividualEditorTemplate(BaseEditorSlave):
    model_iface = IIndividual
    gladefile = 'BaseTemplate'


    def __init__(self, conn, model=None, person_slave=None,
                 visual_mode=False):
        self._person_slave = person_slave
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)

    def get_person_slave(self):
        return self._person_slave

    def attach_person_slave(self, slave):
        self._person_slave.attach_slave('person_status_holder', slave)

    #
    # BaseEditorSlave hooks
    #

    def setup_slaves(self):
        if not self._person_slave:
            klass = _PersonEditorTemplate
            self._person_slave = klass(self.conn, self.model.person,
                                       visual_mode=self.visual_mode)
            self.attach_slave('main_holder', self._person_slave)

        slave = self._person_slave
        slave_class = IndividualDocuments
        self.documents_slave = slave.attach_model_slave('individual_holder',
                                                        slave_class,
                                                        self.model)
        holder_name = 'details_holder'
        slave_class = IndividualDetailsSlave
        self.details_slave = slave.attach_model_slave(holder_name,
                                                      slave_class,
                                                      self.model)

    def on_confirm(self, confirm_person=True):
        self.details_slave.on_confirm()
        if confirm_person:
            self._person_slave.on_confirm()
        return self.model


class _CompanyEditorTemplate(BaseEditorSlave):
    model_iface = ICompany
    gladefile = 'BaseTemplate'

    def __init__(self, conn, model=None, person_slave=None,
                 visual_mode=False):
        self._person_slave = person_slave
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)

    def get_person_slave(self):
        return self._person_slave

    def attach_person_slave(self, slave):
        self._person_slave.attach_slave('person_status_holder', slave)

    #
    # BaseEditor hooks
    #

    def setup_slaves(self):
        if not self._person_slave:
            klass = _PersonEditorTemplate
            self._person_slave = klass(self.conn, self.model.person,
                                       visual_mode=self.visual_mode)
            self.attach_slave('main_holder', self._person_slave)

        klass = CompanyDocumentsSlave
        self.company_docs_slave = klass(self.conn, self.model,
                                        visual_mode=self.visual_mode)
        self._person_slave.attach_slave('company_holder',
                                       self.company_docs_slave)

    def on_confirm(self, confirm_person=True):
        if confirm_person:
            self._person_slave.on_confirm()
        return self.model


class BasePersonRoleEditor(BaseEditor):
    """A base class for person role editors. This class can not be
    instantiated directly.
    Notes:
        role_type   = This argument represents one of the following
                      constants of Person domain class: ROLE_INDIVIDUAL
                      or ROLE_COMPANY
    """

    def __init__(self, conn, model=None, role_type=None, person=None,
                 visual_mode=False):
        if not (model or role_type is not None):
            raise ValueError('A role_type attribute is required')
        self.role_type = role_type
        self.person = person
        BaseEditor.__init__(self, conn, model, visual_mode=visual_mode)
        # FIXME: Implement and use IDescribable on the model
        self.set_description(self.model.person.name)

    def get_person_slave(self):
        return self.main_slave.get_person_slave()

    def set_phone_number(self, phone_number):
        slave = self.get_person_slave()
        slave.set_phone_number(phone_number)

    def _check_role_type(self):
        available_types = Person.ROLE_INDIVIDUAL, Person.ROLE_COMPANY
        if not self.role_type in available_types:
            raise ValueError('Invalid value for role_type attribute')

    def _create_company_slave(self, company, person_slave=None):
        klass = _CompanyEditorTemplate
        self.company_slave = klass(self.conn, company,
                                   person_slave=person_slave,
                                   visual_mode=self.visual_mode)
        return self.company_slave

    def _create_individual_slave(self, individual, person_slave=None):
        klass = _IndividualEditorTemplate
        self.individual_slave = klass(self.conn, individual,
                                      person_slave=person_slave,
                                      visual_mode=self.visual_mode)
        return self.individual_slave

    #
    # BaseEditor hooks
    #


    def create_model(self, conn):
        # XXX: Waiting fix for bug 2163. We should not need anymore to
        # provide empty values for mandatory attributes
        if not self.person:
            self.person = Person(name="", connection=conn)
        self._check_role_type()
        if (self.role_type == Person.ROLE_INDIVIDUAL and not
            IIndividual(self.person, None)):
            self.person.addFacet(IIndividual, connection=conn)
        elif (self.role_type == Person.ROLE_COMPANY and not
              ICompany(self.person, None)):
            self.person.addFacet(ICompany, connection=conn)
        else:
            pass
        return self.person

    def setup_slaves(self):
        individual = IIndividual(self.model.person, None)
        company = ICompany(self.model.person, None)

        if not (individual or company):
            raise ValueError('This person must have at least an '
                             'IIndividual or ICompany facets')

        if individual and company:
            slave = self._create_individual_slave(individual)
            person_slave = slave.get_person_slave()
            self._create_company_slave(company, person_slave)

        elif individual:
            slave = self._create_individual_slave(individual)
            self.company_slave = None

        else:
            slave = self._create_company_slave(company)
            self.individual_slave = None

        self.attach_slave('main_holder', slave)
        self.main_slave = slave

    def on_confirm(self):
        if self.individual_slave and self.company_slave:
            self.individual_slave.on_confirm()
            self.company_slave.on_confirm(confirm_person=False)
        elif self.individual_slave:
            self.individual_slave.on_confirm()
        else:
            self.company_slave.on_confirm()
        return self.model
