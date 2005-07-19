# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
"""
gui/search/person.py

    Search dialogs for person objects
"""

from sqlobject.sqlbuilder import INNERJOINOn, LEFTJOINOn, AND
from kiwi.ui.views import SlaveView
from kiwi.ui.widgets.list import Column
from stoqlib.gui.search import SearchEditor
from stoqlib.gui.columns import FacetColumn, ForeignKeyColumn

from stoq.gui.editors.client_editor import ClientEditor
from stoq.gui.editors.person_editor import PersonEditor
from stoq.gui.editors.individual_editor import IndividualEditor
from stoq.gui.editors.company_editor import (CompanyEditor, 
                                             SupplierEditor)
from stoq.gui.editors.employee_editor import EmployeeEditor
from stoq.domain.interfaces import (ICompany, IIndividual, 
                                    IEmployee, ISupplier,
                                    IClient)
from stoq.domain.person import (Person, Address, EmployeePosition,
                                PersonAdaptToIndividual,
                                PersonAdaptToClient,
                                PersonAdaptToCompany,
                                PersonAdaptToSupplier,
                                PersonAdaptToEmployee)


class BasePersonSearch(SearchEditor):
    size = (800,500)
    title = _('Person Search')
    editor_class = None
    table = None
    interface = None
    editor_class = None

    def __init__(self, title='', hide_footer=False):
        self.title = title or self.title
        SearchEditor.__init__(self, self.table, 
                              self.editor_class,
                              interface=self.interface,
                              hide_footer=hide_footer)


class EmployeeSearch(BasePersonSearch):
    title = _('Employee Search')
    editor_class = EmployeeEditor
    table = PersonAdaptToEmployee
    


    #
    # Hooks
    #



    def get_columns(self):
        return [ForeignKeyColumn(Person, 'name', _('Name'), str, 
                                 width=250, obj_field='_original'),
                ForeignKeyColumn(EmployeePosition, 'name', _('Position'), 
                                 str, width=250, obj_field='position'),
                Column('registry_number', _('Registry Number'), str,
                       width=150),
                Column('status_string', _('Status'), str)]

    def get_extra_query(self):
        return PersonAdaptToEmployee.q._originalID == Person.q.id

    def get_query_args(self):
        return dict(join = LEFTJOINOn(PersonAdaptToEmployee, 
                                      EmployeePosition,
                    PersonAdaptToEmployee.q.positionID == EmployeePosition.q.id))


class SupplierSearch(BasePersonSearch):
    title = _('Supplier Search')
    editor_class = SupplierEditor
    table = Person
    interface = ISupplier
    


    #
    # Hooks
    #



    def get_columns(self):
        return [Column('name', _('Name'), str, 
                       sorted=True, width=250), 
                FacetColumn(ICompany, 'fancy_name', _('Fancy Name'), str,
                            width=250),
                FacetColumn(ICompany, 'cnpj', _('CNPJ'), str)]

    def get_extra_query(self):
        q1 = Person.q.id == PersonAdaptToCompany.q._originalID
        q2 = Person.q.id == PersonAdaptToSupplier.q._originalID
        return AND(q1, q2)
        

class ClientSearch(BasePersonSearch):
    title = _('Client Search')
    editor_class = ClientEditor
    table = Person
    interface = IClient
    


    #
    # Hooks
    #



    def get_columns(self):
        return [Column('name', _('Name'), str, 
                         sorted=True, width=250), 
                Column('phone_number', _('Phone Number'), str,
                       width=130),
                FacetColumn(IIndividual, 'cpf', _('CPF'), str,
                            width=130),
                FacetColumn(IIndividual, 'rg_number', _('RG'), str)]

    def get_extra_query(self):
        q1 = Person.q.id == PersonAdaptToIndividual.q._originalID
        q2 = Person.q.id == PersonAdaptToClient.q._originalID
        return AND(q1, q2)


class CompanySearch(BasePersonSearch):
    title = _('Company Search')
    editor_class = CompanyEditor
    table = Person
    interface = ICompany



    #
    # Hooks
    #



    def get_columns(self):
        return [Column('name', _('Name'), str, sorted=True,
                       width=250), 
                FacetColumn(ICompany, 'fancy_name', _('Fancy Name'), str,
                            width=250),
                FacetColumn(ICompany, 'cnpj', _('CNPJ'), str)]

    def get_query_args(self):
        return dict(join = INNERJOINOn(Person, PersonAdaptToCompany,
                        Person.q.id == PersonAdaptToCompany.q._originalID))


class IndividualSearch(BasePersonSearch):
    title = _('Individual Search')
    editor_class = IndividualEditor
    table = Person
    interface = IIndividual
    


    #
    # Hooks
    #



    def get_columns(self):
        return [Column('name', _('Name'), str, sorted=True,
                       width=250), 
                Column('phone_number', _('Phone Number'), str,
                       width=130),
                FacetColumn(IIndividual, 'cpf', _('Cpf'), str,
                            width=130),
                FacetColumn(IIndividual, 'rg_number', _('RG'), str)]

    def get_query_args(self):
        return dict(join = INNERJOINOn(Person, PersonAdaptToIndividual,
                    Person.q.id == PersonAdaptToIndividual.q._originalID))
                             

class PersonSearch(BasePersonSearch):
    title = _('Person Search')
    editor_class = PersonEditor
    table = Person



    #
    # Hooks
    #



    def get_columns(self):
        return [Column('name', _('Name'), str, sorted=True, width=250), 
                Column('phone_number', _('Phone Number'), str, width=120),
                Column('mobile_number', _('Mobile Number'), str, width=120),
                ForeignKeyColumn(Address, 'street', _('Street'), 
                                 str, obj_field='main_address')]

    def get_query_args(self):
        return dict(join = LEFTJOINOn(Person, Address,
                    Person.q.id == Address.q.personID))
