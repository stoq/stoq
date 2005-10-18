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
"""
gui/search/person.py

    Search dialogs for person objects
"""

import gettext

from sqlobject.sqlbuilder import LEFTJOINOn, AND
from kiwi.ui.widgets.list import Column
from stoqlib.gui.search import SearchEditor
from stoqlib.gui.columns import FacetColumn, ForeignKeyColumn

from stoq.gui.editors.client import ClientEditor
from stoq.gui.editors.supplier import SupplierEditor
from stoq.gui.editors.employee import EmployeeEditor
from stoq.domain.interfaces import (ICompany, IIndividual, 
                                    ISupplier, IClient)
from stoq.domain.person import (Person, EmployeePosition,
                                PersonAdaptToIndividual,
                                PersonAdaptToClient,
                                PersonAdaptToCompany,
                                PersonAdaptToSupplier,
                                PersonAdaptToEmployee)

_ = gettext.gettext

class BasePersonSearch(SearchEditor):
    size = (800,500)
    title = _('Person Search')
    editor_class = None
    table = None
    interface = None
    editor_class = None
    search_lbl_text = None
    result_strings = None

    def __init__(self, title='', hide_footer=False,
                 parent_conn=None):
        self.title = title or self.title
        SearchEditor.__init__(self, self.table, 
                              self.editor_class,
                              interface=self.interface,
                              parent_conn=parent_conn,
                              hide_footer=hide_footer)
        self.set_searchbar_labels(self.search_lbl_text)
        self.set_result_strings(*self.result_strings)
                


class EmployeeSearch(BasePersonSearch):
    title = _('Employee Search')
    editor_class = EmployeeEditor
    table = PersonAdaptToEmployee
    search_lbl_text = _('Employees Matching:')
    result_strings = _('employee'), _('employees')
    


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
    search_lbl_text = _('Suppliers Matching:')
    result_strings = _('supplier'), _('suppliers')
    


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
    search_lbl_text = _('Clients Matching:')
    result_strings = _('client'), _('clients')
    


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
