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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Ariqueli Tejada Fonseca     <aritf@async.com.br>
##
""" Search dialogs for person objects """

from sqlobject.sqlbuilder import LEFTJOINOn, AND, OR
from kiwi.ui.widgets.list import Column
from kiwi.argcheck import argcheck

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.validators import format_phone_number
from stoqlib.gui.editors.personeditor import (ClientEditor, SupplierEditor,
                                              EmployeeEditor,
                                              TransporterEditor,
                                              EmployeeRoleEditor, BranchEditor,
                                              CardProviderEditor,
                                              FinanceProviderEditor)
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.columns import FacetColumn, ForeignKeyColumn
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.slaves.filterslave import FilterSlave
from stoqlib.domain.interfaces import (ICompany, ISupplier, IEmployee,
                                       IClient, ICreditProvider,
                                       ITransporter, IBranch)
from stoqlib.domain.person import (Person, EmployeeRole, ClientView,
                                   PersonAdaptToEmployee)
from stoqlib.gui.wizards.personwizard import run_person_role_dialog

_ = stoqlib_gettext


class BasePersonSearch(SearchEditor):
    size = (750, 500)
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
    table = PersonAdaptToEmployee
    search_lbl_text = _('matching:')
    result_strings = _('employee'), _('employees')
    filter_label = _('Show employees with status')

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        employees = [(value, key) for key, value in
                     self.table.statuses.items()]
        employees.insert(0, (_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(employees, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(self.filter_label)
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                   self.search_bar.search_items)

    def get_columns(self):
        return [ForeignKeyColumn(Person, 'name', _('Name'), str,
                                 width=250, adapted=True,
                                 expand=True),
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
        return dict(join=LEFTJOINOn(
            self.table, EmployeeRole,
            self.table.q.roleID == EmployeeRole.q.id))

    def get_searchlist_model(self, model):
        return IEmployee(model)


class SupplierSearch(BasePersonSearch):
    title = _('Supplier Search')
    editor_class = SupplierEditor
    size = (750, 450)
    table = Person
    interface = ISupplier
    search_lbl_text = _('Suppliers Matching:')
    result_strings = _('supplier'), _('suppliers')

    #
    # Hooks
    #

    def get_columns(self):
        return [Column('name', _('Name'), str,
                       sorted=True, width=250, expand=True),
                Column('phone_number', _('Phone Number'), str,
                       format_func=format_phone_number, width=110),
                FacetColumn(ICompany, 'fancy_name', _('Fancy Name'), str,
                            width=180),
                FacetColumn(ICompany, 'cnpj', _('CNPJ'), str, width=140)]

    def get_extra_query(self):
        supplier_table = Person.getAdapterClass(ISupplier)
        return Person.q.id == supplier_table.q._originalID

    def get_query_args(self):
        company_table = Person.getAdapterClass(ICompany)
        return dict(join=LEFTJOINOn(
            Person, company_table,
            Person.q.id == company_table.q._originalID))


class AbstractCreditProviderSearch(BasePersonSearch):
    title = ""
    table = Person
    interface = ICreditProvider
    search_lbl_text = ''
    result_strings = None
    editor_class = None

    def __init__(self, conn, title='', hide_footer=True):
        self.provider_table = self.table.getAdapterClass(ICreditProvider)
        BasePersonSearch.__init__(self, conn, title, hide_footer)

    def get_columns(self):
        return [Column('name', title=_('Name'),
                       data_type=str, sorted=True, expand=True),
                Column('phone_number', _('Phone Number'), str,
                       format_func=format_phone_number, width=130),
                FacetColumn(ICreditProvider, 'short_name',
                            title=_('Short Name'), data_type=str,
                            width=150),
                FacetColumn(ICreditProvider, 'is_active',
                            title=_('Active'), data_type=bool,
                            editable=True)]

    def on_cell_edited(self, klist, obj, attr):
        conn = obj.get_connection()
        conn.commit()

    def get_provider_type(self):
        raise NotImplementedError("This method must be defined on child")

    def get_extra_query(self):
        q1 = self.table.q.id == self.provider_table.q._originalID
        q2 = self.provider_table.q.provider_type == self.get_provider_type()
        return AND(q1, q2)


class CardProviderSearch(AbstractCreditProviderSearch):
    title = _('Card Provider Search')
    search_lbl_text = _('Card providers matching:')
    result_strings = _('card provider'), _('card providers')
    editor_class = CardProviderEditor

    def get_provider_type(self):
        return self.provider_table.PROVIDER_CARD


class FinanceProviderSearch(AbstractCreditProviderSearch):
    title = _('Finance Provider Search')
    search_lbl_text = _('Finance providers matching:')
    result_strings = _('finance provider'), _('finance providers')
    editor_class = FinanceProviderEditor

    def get_provider_type(self):
        return self.provider_table.PROVIDER_FINANCE


class ClientSearch(BasePersonSearch):
    title = _('Client Search')
    editor_class = ClientEditor
    table = ClientView
    search_lbl_text = _('matching:')
    result_strings = _('client'), _('clients')

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        client_table = Person.getAdapterClass(IClient)
        statuses = [(value, key) for key, value in
                    client_table.statuses.items()]
        statuses.insert(0, (_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(statuses, selected=ALL_ITEMS_INDEX)
        filter_label = _('Show clients with status')
        self.filter_slave.set_filter_label(filter_label)
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)

    @argcheck(ClientView)
    def get_editor_model(self, client_view):
        return Person.iget(IClient, client_view.client_id,
                           connection=self.conn)

    def get_columns(self):
        return [Column('name', _('Name'), str,
                       sorted=True, width=250, expand=True),
                Column('phone_number', _('Phone Number'), str,
                       format_func=format_phone_number, width=150),
                Column('cpf', _('CPF'), str, width=130),
                Column('rg_number', _('RG'), str, width=120)]

    def get_extra_query(self):
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            return self.table.q.status == status

    def on_details_button_clicked(self, *args):
        items = self.klist.get_selected()
        client = Person.iget(IClient, items.client_id, connection=self.conn)
        run_dialog(ClientDetailsDialog, self, self.conn, client)

    def update_widgets(self, *args):
        items = self.klist.get_selected()
        self.set_details_button_sensitive(items is not None)
        self.set_edit_button_sensitive(items is not None)


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
        items.insert(0, (_('Any Transporters'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show:'))
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)

    def get_columns(self):
        return [Column('name', title=_('Name'),
                       data_type=str, sorted=True, width=300,
                       expand=True),
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
    size = (750, 500)
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
                                 width=200, adapted=True, expand=True),
                ForeignKeyColumn(Person, 'phone_number',
                                 _('Phone Number'), data_type=str,
                                 width=150, adapted=True),
                ForeignKeyColumn(Person, 'name', _('Manager'), data_type=str,
                                 width=250, obj_field='manager'),
                Column('status_str', _('Status'), data_type=str)]

    def get_extra_query(self):
        return OR(Person.q.id == self.table.q.managerID,
                  Person.q.id == self.table.q._originalID)

    def get_searchlist_model(self, person):
        return IBranch(person)

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        statuses = [(value, key)
                    for key, value in self.table.statuses.items()]
        statuses.insert(0, (_('Any'), ALL_ITEMS_INDEX))
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
            raise ValueError(
                'Invalid status for User table. got %s' % status)
