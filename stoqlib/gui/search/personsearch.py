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
""" Search dialogs for person objects """

from decimal import Decimal

from kiwi.argcheck import argcheck
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.objectlist import Column, SearchColumn
import pango

from stoqlib.api import api
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_phone_number
from stoqlib.gui.editors.personeditor import (ClientEditor, SupplierEditor,
                                              EmployeeEditor,
                                              TransporterEditor,
                                              EmployeeRoleEditor, BranchEditor,
                                              CardProviderEditor, UserEditor)
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.dialogs.supplierdetails import SupplierDetailsDialog
from stoqlib.domain.person import (EmployeeRole,
                                   PersonAdaptToBranch, BranchView,
                                   PersonAdaptToClient, ClientView,
                                   PersonAdaptToCreditProvider,
                                   CreditProviderView,
                                   PersonAdaptToEmployee, EmployeeView,
                                   TransporterView,
                                   SupplierView, UserView)
from stoqlib.gui.wizards.personwizard import run_person_role_dialog

_ = stoqlib_gettext


class BasePersonSearch(SearchEditor):
    size = (-1, 500)
    title = _('Person Search')
    editor_class = None
    table = None
    interface = None
    editor_class = None
    search_lbl_text = None
    result_strings = None

    def __init__(self, conn, title='', hide_footer=True):
        self.title = title or self.title
        SearchEditor.__init__(self, conn, self.table,
                              self.editor_class,
                              interface=self.interface,
                              hide_footer=hide_footer)
        self.set_searchbar_labels(self.search_lbl_text)
        self.set_result_strings(*self.result_strings)

    def run_dialog(self, editor_class, parent, *args):
        return run_person_role_dialog(editor_class, parent, *args)


class EmployeeSearch(BasePersonSearch):
    title = _('Employee Search')
    editor_class = EmployeeEditor
    table = EmployeeView
    search_lbl_text = _('matching:')
    result_strings = _('employee'), _('employees')

    def _get_status_values(self):
        items = [(value, key) for key, value in
                 PersonAdaptToEmployee.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    def _get_role_values(self):
        items = [(role.name, role.name) for role in
                 EmployeeRole.select()]
        items.insert(0, (_('Any'), None))
        return items

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['name', 'role', 'registry_number'])
        status_filter = ComboSearchFilter(_('Show employees with status'),
                                          self._get_status_values())
        self.add_filter(status_filter, SearchFilterPosition.TOP, ['status'])

    def get_columns(self):
        return [SearchColumn('name', _('Name'), str, expand=True),
                SearchColumn('role', _('Role'), str, width=225,
                             valid_values=self._get_role_values()),
                SearchColumn('registry_number', _('Registry Number'), str),
                SearchColumn('status_string', _('Status'), str,
                             valid_values=self._get_status_values(),
                             search_attribute='status')]

    def get_editor_model(self, model):
        return model.employee


class SupplierSearch(BasePersonSearch):
    title = _('Supplier Search')
    editor_class = SupplierEditor
    size = (800, 450)
    table = SupplierView
    search_lbl_text = _('Suppliers Matching:')
    result_strings = _('supplier'), _('suppliers')

    def __init__(self, conn, **kwargs):
        self.company_doc_l10n = api.get_l10n_field(conn, 'company_document')
        SearchEditor.__init__(self, conn, **kwargs)

    #
    # SearchDialog hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['name', 'phone_number', 'cnpj'])

    def get_columns(self):
        return [SearchColumn('name', _('Name'), str,
                             sorted=True, expand=True),
                SearchColumn('phone_number', _('Phone Number'), str,
                             format_func=format_phone_number, width=110),
                SearchColumn('fancy_name', _('Fancy Name'), str,
                             width=180),
                SearchColumn('cnpj', self.company_doc_l10n.label,
                             str, width=140)]

    def on_details_button_clicked(self, *args):
        selected = self.results.get_selected()
        run_dialog(SupplierDetailsDialog, self, self.conn, selected.supplier)

    def update_widgets(self, *args):
        supplier_view = self.results.get_selected()
        self.set_details_button_sensitive(supplier_view is not None)
        self.set_edit_button_sensitive(supplier_view is not None)

    def get_editor_model(self, supplier_view):
        return supplier_view.supplier


class AbstractCreditProviderSearch(BasePersonSearch):
    title = ""
    table = CreditProviderView
    search_lbl_text = ''
    result_strings = None
    editor_class = None
    provider_type = None

    def __init__(self, conn, title='', hide_footer=True):
        self.provider_table = PersonAdaptToCreditProvider
        BasePersonSearch.__init__(self, conn, title, hide_footer)
        self.results.connect('cell-edited', self._on_results__cell_edited)

    def create_filters(self):
        self.set_text_field_columns(['name', 'phone_number', 'short_name'])
        self.executer.add_query_callback(self._get_query)

    def get_columns(self):
        return [SearchColumn('name', title=_('Name'),
                             data_type=str, sorted=True, expand=True),
                SearchColumn('phone_number', _('Phone Number'), str,
                             format_func=format_phone_number, width=130),
                SearchColumn('short_name', _('Short Name'), str,
                             width=150),
                SearchColumn('is_active', _('Active'), data_type=bool,
                             editable=True),
                SearchColumn('credit_fee', _('Credit Fee'), data_type=Decimal,
                             width=90, visible=False),
                SearchColumn('debit_fee', _('Debit Fee'), data_type=Decimal,
                             width=90, visible=False),
                SearchColumn('credit_installments_store_fee',
                             _('Credit installments store Fee'), data_type=Decimal,
                             expand=True, visible=False),
                SearchColumn('credit_installments_provider_fee',
                             _('Credit installments provider Fee'),
                             data_type=Decimal, expand=True, visible=False),
                SearchColumn('debit_pre_dated_fee', _('Debit pre-dated fee'),
                             data_type=Decimal, width=190, visible=False),
                SearchColumn('monthly_fee', _('Fixed fee'),
                             data_type=Decimal, width=100, visible=False)]

    def get_editor_model(self, provider_view):
        return provider_view.provider

    def _get_query(self, states):
        return self.provider_table.q.provider_type == self.provider_type

    def _on_results__cell_edited(self, results, obj, attr):
        trans = api.new_transaction()
        cards = trans.get(obj.provider)
        cards.is_active = obj.is_active
        trans.commit(close=True)


class CardProviderSearch(AbstractCreditProviderSearch):
    title = _('Card Provider Search')
    editor_class = CardProviderEditor
    search_lbl_text = _('matching:')
    result_strings = _('provider'), _('providers')
    provider_type = PersonAdaptToCreditProvider.PROVIDER_CARD


class ClientSearch(BasePersonSearch):
    title = _('Client Search')
    editor_class = ClientEditor
    table = ClientView
    search_lbl_text = _('matching:')
    result_strings = _('client'), _('clients')

    def __init__(self, conn, **kwargs):
        self.company_doc_l10n = api.get_l10n_field(conn, 'company_document')
        SearchEditor.__init__(self, conn, **kwargs)

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['name', 'cpf', 'rg_number', 'phone_number'])
        statuses = [(v, k) for k, v in PersonAdaptToClient.statuses.items()]
        statuses.insert(0, (_('Any'), None))
        status_filter = ComboSearchFilter(_('Show clients with status'),
                                          statuses)
        status_filter.select(None)
        self.add_filter(status_filter, SearchFilterPosition.TOP, ['status'])

    def get_columns(self):
        return [SearchColumn('name', _('Name'), str,
                             sorted=True, expand=True),
                SearchColumn('client_category', _('Category'), str,
                             width=150, visible=False),
                SearchColumn('phone_number', _('Phone Number'), str,
                             format_func=format_phone_number, width=150),
                Column('cnpj_or_cpf', _('Document'), str, width=150),
                SearchColumn('cnpj', self.company_doc_l10n.label, str, width=150, visible=False),
                SearchColumn('cpf', _('CPF'), str, width=130, visible=False),
                SearchColumn('rg_number', _('RG'), str, width=120)]

    @argcheck(ClientView)
    def get_editor_model(self, client_view):
        return client_view.client

    def on_details_button_clicked(self, *args):
        selected = self.results.get_selected()
        run_dialog(ClientDetailsDialog, self, self.conn, selected.client)

    def update_widgets(self, *args):
        client_view = self.results.get_selected()
        self.set_details_button_sensitive(client_view is not None)
        self.set_edit_button_sensitive(client_view is not None)


class TransporterSearch(BasePersonSearch):
    title = _('Transporter Search')
    editor_class = TransporterEditor
    table = TransporterView
    search_lbl_text = _('matching:')
    result_strings = _('transporter'), _('transporters')

    def create_filters(self):
        self.set_text_field_columns(['name', 'phone_number'])
        items = [(_('Active'), True),
                 (_('Inactive'), False)]
        items.insert(0, (_('Any'), None))

        status_filter = ComboSearchFilter(_('Show transporters with status'),
                                          items)
        status_filter.select(None)
        self.add_filter(status_filter, SearchFilterPosition.TOP, ['is_active'])

    def get_columns(self):
        return [SearchColumn('name', title=_('Name'),
                             data_type=str, sorted=True, expand=True),
                SearchColumn('phone_number', _('Phone Number'), str,
                             format_func=format_phone_number, width=180),
                SearchColumn('freight_percentage', _('Freight (%)'), float,
                             width=150)]

    def get_editor_model(self, model):
        return model.transporter


class EmployeeRoleSearch(SearchEditor):
    title = _('Employee Role Search')
    editor_class = EmployeeRoleEditor
    table = EmployeeRole
    size = (-1, 390)
    advanced_search = False

    def __init__(self, conn):
        SearchEditor.__init__(self, conn, EmployeeRoleSearch.table,
                              EmployeeRoleSearch.editor_class)
        self.set_result_strings(_('role'), _('roles'))

    #
    # SearchEditor Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['name'])
        self.set_searchbar_labels(_('Role Matching'))

    def get_columns(self):
        return [Column('name', _('Role'), str, sorted=True, expand=True)]


class BranchSearch(BasePersonSearch):
    title = _('Branch Search')
    editor_class = BranchEditor
    table = BranchView
    search_lbl_text = _('matching')
    result_strings = (_('branch'), _('branches'))

    #
    # SearchEditor Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['name', 'phone_number'])
        statuses = [(value, key)
                    for key, value in PersonAdaptToBranch.statuses.items()]
        statuses.insert(0, (_('Any'), None))
        status_filter = ComboSearchFilter(_('Show branches with status'),
                                          statuses)
        status_filter.select(None)
        self.executer.add_filter_query_callback(
            status_filter, self._get_status_query)
        self.search.add_filter(status_filter, SearchFilterPosition.TOP)

    def get_columns(self):
        return [SearchColumn('name', _('Name'), str, expand=True),
                SearchColumn('phone_number', _('Phone Number'), str,
                             width=150),
                SearchColumn('manager_name', _('Manager'), str,
                             width=250),
                Column('status_str', _('Status'), data_type=str)]

    def get_editor_model(self, branch_view):
        return branch_view.branch

    #
    # Private
    #

    def _get_status_query(self, state):
        if state.value == PersonAdaptToBranch.STATUS_ACTIVE:
            return PersonAdaptToBranch.q.is_active == True
        elif state.value == PersonAdaptToBranch.STATUS_INACTIVE:
            return PersonAdaptToBranch.q.is_active == False


class UserSearch(BasePersonSearch):
    title = _('User Search')
    editor_class = UserEditor
    size = (750, 450)
    table = UserView
    search_lbl_text = _('Users Matching:')
    result_strings = _('user'), _('users')

    #
    # SearchDialog hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['name', 'profile_name', 'username'])

    def get_columns(self):
        return [SearchColumn('username', title=_('Login Name'), sorted=True,
                              data_type=str, width=150, searchable=True),
                SearchColumn('profile_name', title=_('Profile'),
                             data_type=str, width=120,
                             ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('name', title=_('Name'), data_type=str,
                             expand=True),
                Column('status_str', title=_('Status'), data_type=str,
                       width=80)]

    def on_details_button_clicked(self, *args):
        selected = self.results.get_selected()
        run_dialog(UserEditor, self, self.conn, selected.user)

    def update_widgets(self, *args):
        user_view = self.results.get_selected()
        self.set_details_button_sensitive(user_view is not None)
        self.set_edit_button_sensitive(user_view is not None)

    def get_editor_model(self, user_view):
        return user_view.user
