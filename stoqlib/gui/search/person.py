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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Ariqueli Tejada Fonseca     <aritf@async.com.br>
##
""" Search dialogs for person objects """

from sqlobject.sqlbuilder import LEFTJOINOn, AND, OR
from kiwi.ui.widgets.list import Column

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.validators import format_phone_number
from stoqlib.gui.editors.person import (ClientEditor, SupplierEditor,
                                        EmployeeEditor,
                                        CreditProviderEditor,
                                        TransporterEditor,
                                        EmployeeRoleEditor, BranchEditor)
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.base.columns import FacetColumn, ForeignKeyColumn
from stoqlib.gui.slaves.filter import FilterSlave
from stoqlib.domain.interfaces import (ICompany, IIndividual, ISupplier,
                                       IEmployee, IClient, ICreditProvider,
                                       ITransporter, IBranch)
from stoqlib.domain.person import (Person, EmployeeRole)
from stoqlib.gui.wizards.person import run_person_role_dialog

_ = stoqlib_gettext


class BasePersonSearch(SearchEditor):
    size = (800,500)
    title = _('Person Search')
    editor_class = None
    table = None
    interface = None
    editor_class = None
    search_lbl_text = None
    result_strings = None

    def __init__(self, conn, title='', hide_footer=False):
        self.title = title or self.title
        SearchEditor.__init__(self, conn, self.table,
                              self.editor_class,
                              interface=self.interface,
                              hide_footer=hide_footer)
        self.set_searchbar_labels(self.search_lbl_text)
        self.set_result_strings(*self.result_strings)

    def run_editor(self, obj):
        return run_person_role_dialog(self.editor_class, self,
                                      self.conn, obj)


class EmployeeSearch(BasePersonSearch):
    title = _('Employee Search')
    editor_class = EmployeeEditor
    table = Person.getAdapterClass(IEmployee)
    search_lbl_text = _('matching:')
    result_strings = _('employee'), _('employees')
    filter_label = _('Show employees with status')

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        employees = [(value, key) for key, value in
                     self.table.statuses.items()]
        employees.append((_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(employees, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(self.filter_label)
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                   self.search_bar.search_items)

    def get_columns(self):
        return [ForeignKeyColumn(Person, 'name', _('Name'), str,
                                 width=250, adapted=True),
                ForeignKeyColumn(EmployeeRole, 'name', _('Role'),
                                 str, width=250, obj_field='role'),
                Column('registry_number', _('Registry Number'), str,
                       width=150),
                Column('status_string', _('Status'), str)]

    def get_extra_query(self):
        employee_table = Person.getAdapterClass(IEmployee)
        query = employee_table.q._originalID == Person.q.id
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            query = AND(query, employee_table.q.status == status)
        return query

    def get_query_args(self):
        return dict(join=LEFTJOINOn(self.table, EmployeeRole,
                                    self.table.q.roleID ==
                                    EmployeeRole.q.id))


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
                Column('phone_number', _('Phone Number'), str,
                       format_func=format_phone_number),
                FacetColumn(ICompany, 'fancy_name', _('Fancy Name'), str,
                            width=180),
                FacetColumn(ICompany, 'cnpj', _('CNPJ'), str)]

    def get_extra_query(self):
        supplier_table = Person.getAdapterClass(ISupplier)
        return Person.q.id == supplier_table.q._originalID

    def get_query_args(self):
        company_table = Person.getAdapterClass(ICompany)
        return dict(join=LEFTJOINOn(Person, company_table,
                                    Person.q.id ==
                                    company_table.q._originalID))


class CreditProviderSearch(BasePersonSearch):
    title = _('Credit Provider Search')
    editor_class = CreditProviderEditor
    table = Person
    interface = ICreditProvider
    search_lbl_text = _('matching:')
    result_strings = _('provider'), _('providers')

    def get_filter_slave(self):
        provider_table = Person.getAdapterClass(ICreditProvider)
        items = [(value, key) for key, value in provider_table.provider_types.items()]
        items.append((_('Any provider'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show:'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)

    def get_columns(self):
        return [Column('name', title=_('Name'),
                       data_type=str, sorted=True, width=250),
                Column('phone_number', _('Phone Number'), str,
                       format_func=format_phone_number, width=130),
                FacetColumn(ICreditProvider, 'short_name',
                            title=_('Short Name'), data_type=str,
                            width=150),
                FacetColumn(ICreditProvider, 'provider_type_str',
                            title=_('Provider Type'), data_type=str,
                            width=200)]

    def get_extra_query(self):
        provider_table = self.table.getAdapterClass(ICreditProvider)
        query = self.table.q.id == provider_table.q._originalID
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            query = AND(query, provider_table.q.provider_type == status)
        return query


class ClientSearch(BasePersonSearch):
    title = _('Client Search')
    editor_class = ClientEditor
    table = Person
    interface = IClient
    search_lbl_text = _('matching:')
    result_strings = _('client'), _('clients')

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        client_table = Person.getAdapterClass(IClient)
        statuses = [(value, key) for key, value in
                    client_table.statuses.items()]
        statuses.append((_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(statuses, selected=ALL_ITEMS_INDEX)
        filter_label = _('Show clients with status')
        self.filter_slave.set_filter_label(filter_label)
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)

    def get_columns(self):
        return [Column('name', _('Name'), str,
                       sorted=True, width=250),
                Column('phone_number', _('Phone Number'), str,
                       format_func=format_phone_number),
                FacetColumn(IIndividual, 'cpf', _('CPF'), str,
                            width=130),
                FacetColumn(IIndividual, 'rg_number', _('RG'), str,
                            width=130),
                FacetColumn(IClient, 'status_string', _('Status'), str)]

    def get_extra_query(self):
        client_table = Person.getAdapterClass(IClient)
        query = Person.q.id == client_table.q._originalID
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            query = AND(query, client_table.q.status == status)
        return query

    def get_query_args(self):
        individual_table = Person.getAdapterClass(IIndividual)
        return dict(join=LEFTJOINOn(Person, individual_table,
                                    Person.q.id ==
                                    individual_table.q._originalID))


class TransporterSearch(BasePersonSearch):
    title = _('Transporter Search')
    editor_class = TransporterEditor
    table = Person
    interface = ITransporter
    search_lbl_text = _('matching:')
    result_strings = _('transporter'), _('transporters')

    def get_filter_slave(self):
        items = [(_('Active Transporters'), True),
                 (_('Inactive Transporters'), False)]
        items.append((_('Any Transporters'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show:'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)

    def get_columns(self):
        return [Column('name', title=_('Name'),
                       data_type=str, sorted=True, width=350),
                Column('phone_number', _('Phone Number'), str,
                       format_func=format_phone_number, width=180),
                FacetColumn(ITransporter, 'freight_percentage',
                            title=_('Freight (%)'), data_type=float,
                            width=150),
                FacetColumn(ITransporter, 'status_string',
                            title=_('Status'), data_type=str)]

    def get_extra_query(self):
        transporter_table = self.table.getAdapterClass(ITransporter)
        query = self.table.q.id == transporter_table.q._originalID
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            query = AND(query, transporter_table.q.is_active == status)
        return query


class EmployeeRoleSearch(SearchEditor):
    title = _('Employee Role Search')
    editor_class = EmployeeRoleEditor
    table = EmployeeRole
    size = (425, 390)

    def __init__(self, conn):
        SearchEditor.__init__(self, conn, EmployeeRoleSearch.table,
                              EmployeeRoleSearch.editor_class)
        self.set_searchbar_labels(_('Role Matching'))
        self.set_result_strings(_('role'), _('roles'))


    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        return [Column('name', _('Role'), str, sorted=True)]


class BranchSearch(BasePersonSearch):
    size = (750,500)
    title = _('Branch Search')
    editor_class = BranchEditor
    table = Person.getAdapterClass(IBranch)
    search_lbl_text = _('matching')
    result_strings = (_('branch'), _('branches'))

    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        return [ForeignKeyColumn(Person, 'name', _('Name'), data_type=str,
                                 width=200, adapted=True),
                ForeignKeyColumn(Person, 'phone_number',
                                 _('Phone Number'), data_type=str,
                                 width=150, adapted=True),
                ForeignKeyColumn(Person, 'name', _('Manager'), data_type=str,
                                 width=250, obj_field='manager'),
                Column('status_str', _('Status'), data_type=str)]

    def get_extra_query(self):
        return OR(Person.q.id == self.table.q.managerID,
                  Person.q.id == self.table.q._originalID)

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        statuses = [(value, key) for key, value in
                    self.table.statuses.items()]
        statuses.append((_('Any'), ALL_ITEMS_INDEX))
        filter_label = _('Show branches with status')
        self.filter_slave = FilterSlave(statuses, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(filter_label)
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)

    def filter_results(self, branches):
        status = self.filter_slave.get_selected_status()
        if status == ALL_ITEMS_INDEX:
            return branches
        elif status == self.table.STATUS_ACTIVE:
            return [branch for branch in branches if branch.is_active]
        elif status == self.table.STATUS_INACTIVE:
            return [branch for branch in branches if not branch.is_active]
        else:
            raise ValueError('Invalid status for User table. got %s'
                             % status)
