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

import datetime
from decimal import Decimal

from kiwi.ui.objectlist import Column
from kiwi.currency import currency
import pango
from storm.expr import Eq

from stoqlib.api import api
from stoqlib.domain.person import (EmployeeRole,
                                   Branch, BranchView,
                                   Client, ClientView,
                                   Employee, EmployeeView,
                                   TransporterView,
                                   SupplierView, UserView, ClientsWithCreditView)
from stoqlib.domain.sale import ClientsWithSaleView, Sale
from stoqlib.domain.sellable import Sellable, SellableCategory
from stoqlib.enums import SearchFilterPosition
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_phone_number, format_quantity
from stoqlib.gui.editors.personeditor import (ClientEditor, SupplierEditor,
                                              EmployeeEditor,
                                              TransporterEditor,
                                              EmployeeRoleEditor, BranchEditor,
                                              UserEditor)
from stoqlib.gui.search.searcheditor import SearchEditor
from stoqlib.gui.search.searchfilters import (ComboSearchFilter,
                                              DateSearchFilter, Today)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.dialogs.supplierdetails import SupplierDetailsDialog
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.search.searchcolumns import SearchColumn
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.reporting.person import ClientsWithSaleReport

_ = stoqlib_gettext


class BasePersonSearch(SearchEditor):
    size = (-1, 500)
    title = _('Person Search')
    search_spec = None
    interface = None
    editor_class = None

    def __init__(self, store, title='', hide_footer=True):
        self.title = title or self.title
        SearchEditor.__init__(self, store,
                              self.editor_class,
                              interface=self.interface,
                              hide_footer=hide_footer)

    def run_dialog(self, editor_class, parent, *args, **kwargs):
        return run_person_role_dialog(editor_class, parent, *args, **kwargs)


class EmployeeSearch(BasePersonSearch):
    title = _('Employee Search')
    editor_class = EmployeeEditor
    search_spec = EmployeeView
    text_field_columns = [EmployeeView.name, EmployeeView.role,
                          EmployeeView.registry_number]

    def _get_status_values(self):
        items = [(value, key) for key, value in
                 Employee.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    def _get_role_values(self):
        items = [(role.name, role.name) for role in
                 self.store.find(EmployeeRole)]
        items.insert(0, (_('Any'), None))
        return items

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        status_filter = ComboSearchFilter(_('Show employees with status'),
                                          self._get_status_values())
        self.add_filter(status_filter, SearchFilterPosition.TOP, ['status'])

    def get_columns(self):
        return [SearchColumn('name', _('Name'), str, expand=True, sorted=True),
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
    search_spec = SupplierView
    search_label = _('Suppliers Matching:')
    text_field_columns = [SupplierView.name, SupplierView.phone_number,
                          SupplierView.cnpj]

    def __init__(self, store, **kwargs):
        self.company_doc_l10n = api.get_l10n_field('company_document')
        SearchEditor.__init__(self, store, **kwargs)

    #
    # SearchDialog hooks
    #

    def get_columns(self):
        return [SearchColumn('name', _('Name'), str,
                             sorted=True, expand=True),
                SearchColumn('phone_number', _('Phone Number'), str,
                             format_func=format_phone_number, width=110),
                # Translators: http://en.wikipedia.org/wiki/Doing_business_as
                SearchColumn('fancy_name', _('DBA'), str,
                             width=180),
                SearchColumn('cnpj', self.company_doc_l10n.label,
                             str, width=140)]

    def on_details_button_clicked(self, *args):
        selected = self.results.get_selected()
        run_dialog(SupplierDetailsDialog, self, self.store, selected.supplier)

    def update_widgets(self, *args):
        supplier_view = self.results.get_selected()
        self.set_details_button_sensitive(supplier_view is not None)
        self.set_edit_button_sensitive(supplier_view is not None)

    def get_editor_model(self, supplier_view):
        return supplier_view.supplier


class ClientSearch(BasePersonSearch):
    title = _('Client Search')
    editor_class = ClientEditor
    search_spec = ClientView
    search_label = _('matching:')
    text_field_columns = [ClientView.name, ClientView.cpf, ClientView.rg_number,
                          ClientView.phone_number, ClientView.mobile_number]

    def __init__(self, store, birth_date=None, **kwargs):
        self._birth_date = birth_date
        self.company_doc_l10n = api.get_l10n_field('company_document')
        self.person_doc_l10n = api.get_l10n_field('person_document')
        SearchEditor.__init__(self, store, **kwargs)

    def setup_widgets(self):
        self.add_csv_button(_("Client"), _("client"))

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        statuses = [(v, k) for k, v in Client.statuses.items()]
        statuses.insert(0, (_('Any'), None))
        status_filter = ComboSearchFilter(_('Show clients with status'),
                                          statuses)
        status_filter.select(None)
        self.add_filter(status_filter, SearchFilterPosition.TOP, ['status'])

        if self._birth_date:
            birthday_filter = self.search.add_filter_by_attribute(
                'birth_date', _('Birthday'), datetime.date,
                callback=self.birthday_search)
            # FIXME: The fifth position is a search by day. This is done
            # elsewhere too but we should not hardcode it. Try to
            # find a better solution in the future and fix everything
            birthday_filter.mode.select_item_by_position(5)
            birthday_filter.start_date.set_date(self._birth_date)
            self.search.refresh()

    def get_columns(self):
        return [SearchColumn('name', _('Name'), str,
                             sorted=True, expand=True),
                SearchColumn('client_category', _('Category'), str,
                             width=150, visible=False),
                SearchColumn('phone_number', _('Phone Number'), str,
                             format_func=format_phone_number, width=150),
                SearchColumn('mobile_number', _('Mobile Number'), str,
                             format_func=format_phone_number, width=150,
                             visible=False),
                Column('cnpj_or_cpf', _('Document'), str, width=150),
                SearchColumn('cnpj', self.company_doc_l10n.label, str, width=150, visible=False),
                SearchColumn('cpf', self.person_doc_l10n.label, str, width=130, visible=False),
                SearchColumn('rg_number', _('RG'), str, width=120),
                SearchColumn('birth_date', _('Birth Date'), datetime.date,
                             visible=False, search_func=self.birthday_search,
                             search_label=_('Birthday'))]

    def get_editor_model(self, client_view):
        return client_view.client

    def on_details_button_clicked(self, *args):
        selected = self.results.get_selected()
        run_dialog(ClientDetailsDialog, self, self.store, selected.client)

    def update_widgets(self, *args):
        client_view = self.results.get_selected()
        self.set_details_button_sensitive(client_view is not None)
        self.set_edit_button_sensitive(client_view is not None)


class TransporterSearch(BasePersonSearch):
    title = _('Transporter Search')
    editor_class = TransporterEditor
    search_spec = TransporterView
    search_label = _('matching:')
    text_field_columns = [TransporterView.name, TransporterView.phone_number]

    def create_filters(self):
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
                SearchColumn('freight_percentage', _('Freight (%)'), Decimal,
                             width=150)]

    def get_editor_model(self, model):
        return model.transporter


class EmployeeRoleSearch(SearchEditor):
    title = _('Employee Role Search')
    editor_class = EmployeeRoleEditor
    search_spec = EmployeeRole
    search_label = _('Role Matching')
    size = (-1, 390)
    advanced_search = False
    text_field_columns = [EmployeeRole.name]

    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        return [Column('name', _('Role'), str, sorted=True, expand=True)]


class BranchSearch(BasePersonSearch):
    title = _('Branch Search')
    editor_class = BranchEditor
    search_spec = BranchView
    search_label = _('matching')
    text_field_columns = [BranchView.name, BranchView.acronym,
                          BranchView.phone_number]

    #
    # SearchEditor Hooks
    #

    def create_filters(self):
        statuses = [(value, key)
                    for key, value in Branch.statuses.items()]
        statuses.insert(0, (_('Any'), None))
        status_filter = ComboSearchFilter(_('Show branches with status'),
                                          statuses)
        status_filter.select(None)
        executer = self.search.get_query_executer()
        executer.add_filter_query_callback(
            status_filter, self._get_status_query)
        self.search.add_filter(status_filter, SearchFilterPosition.TOP)

    def get_columns(self):
        return [SearchColumn('name', _('Name'), str, expand=True, sorted=True),
                SearchColumn('fancy_name', _('Fancy name'), str, expand=True,
                             visible=False),
                SearchColumn('acronym', _('Acronym'), data_type=str,
                             visible=False),
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
        if state.value == Branch.STATUS_ACTIVE:
            return Eq(Branch.is_active, True)
        elif state.value == Branch.STATUS_INACTIVE:
            return Eq(Branch.is_active, False)


class UserSearch(BasePersonSearch):
    title = _('User Search')
    editor_class = UserEditor
    size = (750, 450)
    search_spec = UserView
    search_label = _('Users Matching:')
    text_field_columns = [UserView.name, UserView.profile_name,
                          UserView.username]

    #
    # SearchDialog hooks
    #

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
        # FIXME: Person editor/slaves are depending on the store being a
        # StoqlibStore. See bug 5012
        with api.new_store() as store:
            selected = self.results.get_selected()
            user = store.fetch(selected.user)
            run_dialog(UserEditor, self, store, user, visual_mode=True)

    def update_widgets(self, *args):
        user_view = self.results.get_selected()
        self.set_details_button_sensitive(user_view is not None)
        self.set_edit_button_sensitive(user_view is not None)

    def get_editor_model(self, user_view):
        return user_view.user


class ClientsWithSaleSearch(SearchDialog):
    title = _(u"Clients with Sale")
    search_spec = ClientsWithSaleView
    report_class = ClientsWithSaleReport
    size = (800, 450)
    unlimited_results = True
    branch_filter_column = Sale.branch_id
    text_field_columns = [ClientsWithSaleView.person_name,
                          ClientsWithSaleView.phone,
                          ClientsWithSaleView.category]

    def setup_widgets(self):
        self.add_csv_button(_('Clients With Sales'), _('clients'))
        self.update_widgets()

    def create_filters(self):
        # Extra filters (that are not columns)
        self.search.add_filter_option(SellableCategory.description,
                                      title=_(u"Product category"),
                                      data_type=str)
        self.search.add_filter_option(Sellable.description,
                                      title=_(u"Product"),
                                      data_type=str)

        # Date
        date_filter = DateSearchFilter(_('Date:'))
        date_filter.select(Today)
        self.add_filter(date_filter, columns=[Sale.confirm_date])

    def get_columns(self, *args):
        return [SearchColumn('person_name', title=_(u"Client"), data_type=str,
                             expand=True, sorted=True),
                SearchColumn('email', title=_(u"Email"), data_type=str,
                             visible=False),
                SearchColumn('phone', title=_(u"Phone"), data_type=str,
                             visible=False),
                SearchColumn('category', title=_(u"Client category"), data_type=str,
                             visible=False),
                Column('cnpj_or_cpf', title=_(u"Document"), data_type=str,
                       visible=False),
                Column('address_string', title=_(u"Address"), data_type=str, visible=False),
                Column('details_string', title=_(u"City"), data_type=str, visible=False),
                SearchColumn('cpf', title=_(u"CPF"), data_type=str,
                             visible=False),
                SearchColumn('cnpj', title=_(u"CNPJ"), data_type=str,
                             visible=False),
                SearchColumn('birth_date', _('Birth Date'), datetime.date,
                             visible=False, search_func=self.birthday_search,
                             search_label=_('Birthday')),
                Column('last_purchase', title=_(u"Last purchase"),
                       data_type=datetime.date),
                Column('sales', title=_(u"# Sales"), data_type=int),
                Column('sale_items', title=_(u"# Items"), data_type=Decimal,
                       format_func=format_quantity,),
                Column('total_amount', title=_(u"Total Amount"), data_type=currency)]

    def update_widgets(self):
        client_view = self.results.get_selected()
        self.set_details_button_sensitive(client_view is not None)

    # Callbacks
    def on_details_button_clicked(self, *args):
        selected = self.results.get_selected()
        client = self.store.find(Client, Client.person_id == selected.id).one()
        run_dialog(ClientDetailsDialog, self, self.store, client)


class ClientsWithCreditSearch(SearchDialog):
    title = _(u"Clients with Credit")
    search_spec = ClientsWithCreditView
    size = (800, 450)
    fast_iter = True
    unlimited_results = True
    text_field_columns = [ClientsWithCreditView.name]

    def setup_widgets(self):
        self.add_csv_button(self.title, _('clients'))
        self.update_widgets()

    def get_columns(self, *args):
        return [SearchColumn('name', title=_(u"Client"), data_type=str,
                             expand=True, sorted=True),
                SearchColumn('email', title=_(u"Email"), data_type=str,
                             visible=False),
                SearchColumn('phone', title=_(u"Phone"), data_type=str,
                             visible=False),
                SearchColumn('category', title=_(u"Category"), data_type=str,
                             visible=False),
                Column('cnpj_or_cpf', title=_(u"Document"), data_type=str,
                       visible=False),
                SearchColumn('cpf', title=_(u"CPF"), data_type=str,
                             visible=False),
                SearchColumn('cnpj', title=_(u"CNPJ"), data_type=str,
                             visible=False),
                SearchColumn('credit_received', title=_(u"Received"),
                             data_type=currency),
                SearchColumn('credit_spent', title=_(u"Spent"),
                             data_type=currency),
                SearchColumn('remaining_credit', title=_(u"Available"),
                             data_type=currency)]

    def update_widgets(self):
        client_view = self.results.get_selected()
        self.set_details_button_sensitive(client_view is not None)

    # Callbacks
    def on_details_button_clicked(self, *args):
        selected = self.results.get_selected()
        client = self.store.get(Client, selected.id)
        run_dialog(ClientDetailsDialog, self, self.store, client)
