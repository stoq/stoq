# -*- Mode: Python; coding: iso-8859-1 -*-
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Templates implementation for person editors.  """


import gettext

import gtk

from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.editors import BaseEditorSlave, BaseEditor
from stoqlib.gui.base.slaves import NoteSlave
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.domain.interfaces import IIndividual, ICompany
from stoqlib.domain.person import Person, CityLocation
from stoqlib.gui.editors.address import AddressAdditionDialog
from stoqlib.gui.slaves.liaison import LiaisonListDialog
from stoqlib.gui.slaves.address import AddressSlave
from stoqlib.gui.slaves.company import CompanyDocumentsSlave
from stoqlib.gui.slaves.individual import (IndividualDetailsSlave,
                                           IndividualDocuments)

_ = gettext.gettext


class PersonEditorTemplate(BaseEditorSlave):
    model_type = Person
    gladefile = 'PersonEditorTemplate'

    left_proxy_widgets = (
        'name',
        'phone_number',
        'fax_number'
        )

    proxy_widgets = (
        'mobile_number',
        'email'
        ) + left_proxy_widgets

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

    def create_model(self, conn):
        # XXX: Waiting fix for bug 2163
        return Person(name="", connection=conn)

    def attach_model_slave(self, name, slave_type, slave_model):
        slave = slave_type(self.conn, slave_model)
        self.attach_slave(name, slave)
        return slave

    def _setup_widgets(self):
        facet_individual = IIndividual(self.model, connection=self.conn)
        facet_company = ICompany(self.model, connection=self.conn)
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

        self.size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        for widget_name in PersonEditorTemplate.left_proxy_widgets:
            widget = getattr(self, widget_name)
            self.size_group.add_widget(widget)

    #
    # Kiwi handlers
    #

    def on_address_button__clicked(self, *args):
        addresses = self.model.addresses
        main_address = self.model.get_main_address()
        if addresses and main_address:
            addresses.remove(main_address)

        result = run_dialog(AddressAdditionDialog, self, self.conn,
                            addresses, person=self.model)
        if not result:
            return

        new_main_address = None

        for address in result:
            if address.is_main_address:
                new_main_address = address
                if main_address:
                    main_address.is_main_address = False

        if new_main_address:
            self.address_slave.set_model(new_main_address)

    def on_contacts_button__clicked(self, *args):
        run_dialog(LiaisonListDialog, self, self.conn, self.model,
                   self.model.liaisons)

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    PersonEditorTemplate.proxy_widgets)

    def setup_slaves(self):
        main_address = self.model.get_main_address()
        self.address_slave = self.attach_model_slave('address_holder',
                                                     AddressSlave,
                                                     main_address)
        address_widgets = self.address_slave.get_left_widgets()
        for widget in address_widgets:
            self.size_group.add_widget(widget)
        self.attach_model_slave('note_holder', NoteSlave, self.model)

    def on_confirm(self):
        self.address_slave.on_confirm()
        main_address = self.address_slave.model
        main_address.person = self.model
        return self.model


class IndividualEditorTemplate(BaseEditorSlave):
    model_iface = IIndividual
    gladefile = 'BaseTemplate'


    def __init__(self, conn, model=None, person_slave=None):
        self._person_slave = person_slave
        BaseEditorSlave.__init__(self, conn, model)

    def get_person_slave(self):
        return self._person_slave

    def ensure_city_location_objects(self):
        """ This method ensure that, if the city location objects for birth
        location and main address city location has the same contents, only
        one CityLocation object is created. """

        birthloc = self.model.birth_location
        person = self.model.get_adapted()
        main_address = person.get_main_address()
        addrloc = main_address.city_location

        same_contents = (addrloc.city == birthloc.city
                         and addrloc.country == birthloc.country
                         and addrloc.state == birthloc.state)

        if (birthloc.id != addrloc.id) and same_contents:
            main_address.city_location = birthloc
            CityLocation.delete(addrloc.id, connection=self.conn)

    def attach_person_slave(self, slave):
        self._person_slave.attach_slave('person_status_holder', slave)

    #
    # BaseEditorSlave hooks
    #

    def setup_slaves(self):
        if not self._person_slave:
            self._person_slave = PersonEditorTemplate(self.conn,
                                                      self.model.get_adapted())
            self.attach_slave('main_holder', self._person_slave)

        slave_class = IndividualDocuments
        slave = self._person_slave
        self.documents_slave = slave.attach_model_slave('individual_holder',
                                                        slave_class,
                                                        self.model)
        holder_name = 'details_holder'
        slave_class = IndividualDetailsSlave
        slave = self._person_slave
        self.details_slave = slave.attach_model_slave(holder_name,
                                                      slave_class,
                                                      self.model)

    def on_confirm(self, confirm_person=True):
        self.details_slave.on_confirm()
        if confirm_person:
            self._person_slave.on_confirm()
        if self.model.birth_location:
            self.ensure_city_location_objects()
        return self.model


class CompanyEditorTemplate(BaseEditorSlave):
    model_iface = ICompany
    gladefile = 'BaseTemplate'

    def __init__(self, conn, model=None, person_slave=None):
        self._person_slave = person_slave
        BaseEditorSlave.__init__(self, conn, model)

    def get_person_slave(self):
        return self._person_slave

    def attach_person_slave(self, slave):
        self._person_slave.attach_slave('person_status_holder', slave)

    def setup_slaves(self):
        if not self._person_slave:
            self._person_slave = PersonEditorTemplate(self.conn,
                                                      self.model.get_adapted())
            self.attach_slave('main_holder', self._person_slave)

        self.company_docs_slave = CompanyDocumentsSlave(self.conn,
                                                        self.model)
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

    def __init__(self, conn, model=None, role_type=None, person=None):
        if not (model or role_type is not None):
            raise ValueError('A role_type attribute is required')
        self.role_type = role_type
        self.person = person
        BaseEditor.__init__(self, conn, model)

    def get_title_model_attribute(self, model):
        return model.get_adapted().name

    def get_person_slave(self):
        return self.main_slave.get_person_slave()

    def _check_role_type(self):
        available_types = Person.ROLE_INDIVIDUAL, Person.ROLE_COMPANY
        if not self.role_type in available_types:
            raise ValueError('Invalid value for role_type attribute')

    def create_model(self, conn):
        # XXX: Waiting fix for bug 2163. We should not need anymore to
        # provide empty values for mandatory attributes
        if not self.person:
            self.person = Person(name="", connection=conn)
        self._check_role_type()
        if (self.role_type == Person.ROLE_INDIVIDUAL and not
            IIndividual(self.person, connection=conn)):
            self.person.addFacet(IIndividual, connection=conn)
        elif (self.role_type == Person.ROLE_COMPANY and not
              ICompany(self.person, connection=conn)):
            self.person.addFacet(ICompany, connection=conn)
        else:
            pass
        return self.person

    def setup_slaves(self):
        individual = IIndividual(self.model.get_adapted(),
                                 connection=self.conn)
        company = ICompany(self.model.get_adapted(), connection=self.conn)

        if not (individual or company):
            raise ValueError('This person must have at least an '
                             'IIndividual or ICompany facets')

        if individual and company:
            self.individual_slave = IndividualEditorTemplate(self.conn,
                                                             individual)
            slave = self.individual_slave
            person_slave = self.individual_slave.get_person_slave()
            self.company_slave = CompanyEditorTemplate(self.conn,
                                                       company, person_slave)
        elif individual:
            self.individual_slave = IndividualEditorTemplate(self.conn,
                                                             individual)
            slave = self.individual_slave
            self.company_slave = None
        else:
            self.company_slave = CompanyEditorTemplate(self.conn, company)
            slave = self.company_slave
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
