# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Main gui definition for admin application.  """

import logging
import operator

from gi.repository import Gtk, GLib

from stoqlib.api import api
from stoqlib.domain.invoice import InvoiceLayout
from stoq.lib.gui.dialogs.certificatedialog import CertificateListDialog
from stoq.lib.gui.dialogs.clientcategorydialog import ClientCategoryDialog
from stoq.lib.gui.dialogs.devices import DeviceSettingsDialog
from stoq.lib.gui.editors.formfieldeditor import FormFieldEditor
from stoq.lib.gui.dialogs.invoicedialog import InvoiceLayoutDialog, InvoicePrinterDialog
from stoq.lib.gui.dialogs.paymentcategorydialog import PaymentCategoryDialog
from stoq.lib.gui.dialogs.paymentmethod import PaymentMethodsDialog
from stoq.lib.gui.dialogs.personmergedialog import PersonMergeDialog
from stoq.lib.gui.dialogs.pindialog import PinDialog
from stoq.lib.gui.dialogs.pluginsdialog import PluginManagerDialog
from stoq.lib.gui.dialogs.sellabledialog import SellableTaxConstantsDialog
from stoq.lib.gui.dialogs.sintegradialog import SintegraDialog
from stoq.lib.gui.editors.personeditor import UserEditor
from stoq.lib.gui.search.costcentersearch import CostCenterSearch
from stoq.lib.gui.search.eventsearch import EventSearch
from stoq.lib.gui.search.fiscalsearch import CfopSearch, FiscalBookEntrySearch
from stoq.lib.gui.search.messagesearch import MessageSearch
from stoq.lib.gui.search.parametersearch import ParameterSearch
from stoq.lib.gui.search.productsearch import ProductSearch
from stoq.lib.gui.search.gridsearch import GridGroupSearch, GridAttributeSearch
from stoq.lib.gui.search.personsearch import (ClientSearch,
                                              EmployeeRoleSearch,
                                              EmployeeSearch,
                                              BranchSearch,
                                              SupplierSearch,
                                              TransporterSearch,
                                              UserSearch)
from stoq.lib.gui.search.profilesearch import UserProfileSearch
from stoq.lib.gui.search.stationsearch import StationSearch
from stoq.lib.gui.search.salesearch import SaleTokenSearch
from stoq.lib.gui.search.servicesearch import ServiceSearch
from stoq.lib.gui.search.taxclasssearch import TaxTemplatesSearch
from stoq.lib.gui.stockicons import (
    STOQ_BOOK, STOQ_BRANCHES, STOQ_CLIENTS,
    STOQ_CONNECT, STOQ_DEVICES, STOQ_TRANSPORTER,
    STOQ_DOCUMENTS, STOQ_EMPLOYEE,
    STOQ_EMPLOYEE_CARD, STOQ_FORMS, STOQ_HR,
    STOQ_MOVEMENT_PRODUCT, STOQ_PARAMETERS,
    STOQ_PAYMENT_CATEGORY, STOQ_PAYMENT_TYPE,
    STOQ_PLUGIN, STOQ_PRINTER, STOQ_PRODUCTS,
    STOQ_SERVICES, STOQ_STATUS_WARNING,
    STOQ_SUPPLIERS, STOQ_SYSTEM, STOQ_TAX_TYPE,
    STOQ_USER_PROFILES)
from stoq.lib.gui.utils.keybindings import get_accels
from stoq.lib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.decorators import public
from stoqlib.lib.message import info
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.translation import locale_sorted, stoqlib_gettext

import stoq
from stoq.gui.shell.shellapp import ShellApp

_ = stoqlib_gettext

logger = logging.getLogger(__name__)

(COL_LABEL,
 COL_NAME,
 COL_PIXBUF) = range(3)


class Tasks(object):
    def __init__(self, app):
        self.app = app

        self.theme = Gtk.IconTheme.get_default()

    def set_model(self, model):
        self.model = model
        self.model.clear()

    def add_defaults(self):
        items = [
            (_('Branches'), 'branches', STOQ_BRANCHES),
            (_('C.F.O.P.'), 'cfop', STOQ_MOVEMENT_PRODUCT),
            (_('Client Categories'), 'client_categories', STOQ_CLIENTS),
            (_('Clients'), 'clients', STOQ_CLIENTS),
            (_('Computers'), 'stations', STOQ_SYSTEM),
            (_('Devices'), 'devices', STOQ_DEVICES),
            (_('Employees'), 'employees', STOQ_EMPLOYEE),
            (_('Events'), 'events', STOQ_STATUS_WARNING),
            (_('Fiscal Books'), 'fiscal_books', STOQ_BOOK),
            (_('Forms'), 'forms', STOQ_FORMS),
            (_('Invoice Printers'), 'invoice_printers', STOQ_PRINTER),
            (_('Parameters'), 'parameters', STOQ_PARAMETERS),
            (_('Payment Categories'), 'payment_categories', STOQ_PAYMENT_CATEGORY),
            (_('Payment Methods'), 'payment_methods', STOQ_PAYMENT_TYPE),
            (_('Plugins'), 'plugins', STOQ_PLUGIN),
            (_('Products'), 'products', STOQ_PRODUCTS),
            (_('Roles'), 'employee_roles', STOQ_EMPLOYEE_CARD),
            (_('Services'), 'services', STOQ_SERVICES),
            (_('Taxes'), 'taxes', STOQ_DOCUMENTS),
            (_('Suppliers'), 'suppliers', STOQ_SUPPLIERS),
            (_('Tax Classes'), 'tax_templates', STOQ_TAX_TYPE),
            (_('Transporters'), 'transporters', STOQ_TRANSPORTER),
            (_('User Profiles'), 'user_profiles', STOQ_USER_PROFILES),
            (_('Users'), 'users', STOQ_HR),
            (_('Connect to Stoq.Link'), 'stoq_link_connect', STOQ_CONNECT),
        ]

        for label, name, pixbuf in locale_sorted(
                items, key=operator.itemgetter(0)):
            self.add_item(label, name, pixbuf)

    @public(since="1.5.0")
    def add_item(self, label, name, pixbuf=None, cb=None):
        """
        @param label: Label to show in the interface
        @param name: Name to use to store internally and use by callbacks
        @param pixbuf: a pixbuf or stock-id/icon-name for the item
        @param cb: callback
        """
        if isinstance(pixbuf, str):
            stock_id = pixbuf
            try:
                pixbuf = self.theme.load_icon(pixbuf, 32, 0)
            except GLib.GError:
                pixbuf = self.app.get_toplevel().render_icon(pixbuf, Gtk.IconSize.DIALOG)
            if pixbuf is not None:
                pixbuf.stock_id = stock_id
        self.model.append([label, name, pixbuf])
        if cb is not None:
            setattr(self, '_open_' + name, cb)

    def on_item_activated(self, icon_view, path):
        name = self.model[path][COL_NAME]
        self.run_task(name)

    def hide_item(self, name):
        for row in self.model:
            if row[COL_NAME] == name:
                del self.model[row.iter]
                break

    def run_task(self, name):
        func = getattr(self, '_open_%s' % name, None)
        if not func:
            logger.info("Couldn't open dialog: %r" % (name, ))
            return
        logger.info("Opening dialog: %r" % (name, ))
        func()

    def _open_branches(self):
        self.app.run_dialog(BranchSearch, self.app.store,
                            hide_footer=True)

    def _open_clients(self):
        self.app.run_dialog(ClientSearch, self.app.store)

    def _open_client_categories(self):
        store = api.new_store()
        model = self.app.run_dialog(ClientCategoryDialog, store)
        store.confirm(model)
        store.close()

    def _open_devices(self):
        self.app.run_dialog(DeviceSettingsDialog, self.app.store)

    def _open_employees(self):
        self.app.run_dialog(EmployeeSearch, self.app.store)

    def _open_employee_roles(self):
        self.app.run_dialog(EmployeeRoleSearch, self.app.store)

    def _open_events(self):
        self.app.run_dialog(EventSearch, self.app.store)

    def _open_forms(self):
        store = api.new_store()
        model = self.app.run_dialog(FormFieldEditor, store)
        store.confirm(model)
        store.close()

    def _open_sale_token(self):
        with api.new_store() as store:
            self.app.run_dialog(SaleTokenSearch, store, hide_footer=True)

    def _open_fiscal_books(self):
        self.app.run_dialog(FiscalBookEntrySearch, self.app.store,
                            hide_footer=True)

    def _open_invoice_layouts(self):
        store = api.new_store()
        model = self.app.run_dialog(InvoiceLayoutDialog, store)
        store.confirm(model)
        store.close()

    def _open_invoice_printers(self):
        if self.app.store.find(InvoiceLayout).is_empty():
            info(_("You must create at least one invoice layout "
                   "before adding an invoice printer"))
            return

        store = api.new_store()
        model = self.app.run_dialog(InvoicePrinterDialog, store)
        store.confirm(model)
        store.close()

    def _open_payment_categories(self):
        store = api.new_store()
        model = self.app.run_dialog(PaymentCategoryDialog, store)
        store.confirm(model)
        store.close()

    def _open_payment_methods(self):
        store = api.new_store()
        model = self.app.run_dialog(PaymentMethodsDialog, store)
        store.confirm(model)
        store.close()

    def _open_parameters(self):
        store = api.new_store()
        model = self.app.run_dialog(ParameterSearch, store)
        store.confirm(model)
        store.close()

    def _open_plugins(self):
        store = api.new_store()
        model = self.app.run_dialog(PluginManagerDialog, store)
        store.confirm(model)
        store.close()

    def _open_products(self):
        self.app.run_dialog(ProductSearch, self.app.store)

    def _open_services(self):
        self.app.run_dialog(ServiceSearch, self.app.store)

    def _open_cfop(self):
        self.app.run_dialog(CfopSearch, self.app.store, hide_footer=True)

    def _open_sintegra(self):
        branch = api.get_current_branch(self.app.store)
        if branch.manager is None:
            info(_(
                "You must define a manager to this branch before you can create"
                " a sintegra archive"))
            return

        self.app.run_dialog(SintegraDialog, self.app.store)

    def _open_stations(self):
        self.app.run_dialog(StationSearch, self.app.store, hide_footer=True)

    def _open_suppliers(self):
        self.app.run_dialog(SupplierSearch, self.app.store)

    def _open_taxes(self):
        self.app.run_dialog(SellableTaxConstantsDialog, self.app.store)

    def _open_tax_templates(self):
        self.app.run_dialog(TaxTemplatesSearch, self.app.store)

    def _open_transporters(self):
        self.app.run_dialog(TransporterSearch, self.app.store)

    def _open_users(self):
        self.app.run_dialog(UserSearch, self.app.store)

    def _open_user_profiles(self):
        self.app.run_dialog(UserProfileSearch, self.app.store)

    def _open_grid_group(self):
        self.app.run_dialog(GridGroupSearch, self.app.store)

    def _open_grid_attribute(self):
        self.app.run_dialog(GridAttributeSearch, self.app.store)

    def _open_ui_form(self):
        self._open_forms()

    def _open_token(self):
        self._open_sale_token()

    def _open_stoq_link_connect(self):
        if stoq.trial_mode:
            return info(_('Online features are not available in trial mode'))
        self.app.run_dialog(PinDialog, self.app.store)

    def _open_certificates(self):
        self.app.run_dialog(CertificateListDialog, None)


class AdminApp(ShellApp):

    app_title = _('Administrative')
    gladefile = "admin"

    ACTION_TASKS = {
        'SearchRole': 'employee_roles',
        'SearchEmployee': 'employees',
        'SearchFiscalBook': 'fiscal_books',
        'SearchCfop': 'cfop',
        'SearchUserProfile': 'user_profiles',
        'SearchUser': 'users',
        'SearchBranch': 'branches',
        'SearchComputer': 'stations',
        'SearchTaxTemplate': 'tax_templates',
        'SearchEvents': 'events',
        'ConfigureGridGroup': 'grid_group',
        'ConfigureGridAttribute': 'grid_attribute',
        'ConfigureDevices': 'devices',
        'ConfigurePaymentMethods': 'payment_methods',
        'ConfigurePaymentCategories': 'payment_categories',
        'ConfigureClientCategories': 'client_categories',
        'ConfigureTaxes': 'taxes',
        'ConfigureUIForm': 'ui_form',
        'ConfigureSaleToken': 'sale_token',
        'ConfigureSintegra': 'sintegra',
        'ConfigureParameters': 'parameters',
        'ConfigureInvoices': 'invoice_layouts',
        'ConfigureInvoicePrinters': 'invoice_printers',
        'ConfigurePlugins': 'plugins',
        'StoqLinkConnect': 'stoq_link_connect',
        'ConfigureCertificates': 'certificates',
    }

    action_permissions = {
        'ConfigureInvoices': ('InvoiceLayout', PermissionManager.PERM_SEARCH),
        'ConfigureInvoicePrinters': ('InvoicePrinter', PermissionManager.PERM_SEARCH),
        'SearchTaxTemplate': ('ProductTaxTemplate', PermissionManager.PERM_SEARCH),
    }

    #
    # Application
    #

    def create_actions(self):
        group = get_accels('app.admin')
        actions = [
            ("SearchRole", None, _("Roles..."),
             group.get('search_roles')),
            ("SearchEmployee", None, _("Employees..."),
             group.get('search_employees')),
            ("SearchEvents", None, _("Events..."),
             group.get('search_events')),
            ("SearchCostCenters", None, _("Cost Centers..."),
             group.get('search_cost_centers')),
            ("SearchDuplicatedPersons", None, _("Duplicated Persons..."),
             None),
            ("SearchCfop", None, _("C.F.O.P..."),
             group.get('search_cfop')),
            ("SearchFiscalBook", None, _("Fiscal books..."),
             group.get('search_fiscalbook')),
            ("SearchUserProfile", None, _("Profiles..."),
             group.get('search_profile')),
            ("SearchUser", None, _("Users..."),
             group.get('search_users')),
            ("SearchBranch", None, _("Branches..."),
             group.get('search_branches')),
            ("SearchComputer", None, _('Computers...'),
             group.get('search_computers')),
            ("SearchTaxTemplate", None, _('Tax Classes...')),
            ("SearchMessages", None, _("Messages...")),
            ("ConfigureMenu", None, _("_Configure")),
            ("ConfigureDevices", None, _("Devices..."),
             group.get('config_devices')),
            ("ConfigureGridGroup", None, _("Attribute Group...")),
            ("ConfigureGridAttribute", None, _("Grid Attribute...")),
            ("ConfigurePaymentMethods", None, _("Payment methods..."),
             group.get('config_payment_methods')),
            ("ConfigurePaymentCategories", None, _("Payment categories..."),
             group.get('config_payment_categories')),
            ("ConfigureClientCategories", None, _("Client categories..."),
             group.get('config_client_categories')),
            ("ConfigureInvoices", None, _("Invoices..."),
             group.get('config_invoices')),
            ("ConfigureInvoicePrinters", None, _("Invoice printers..."),
             group.get('config_invoice_printers')),
            ("ConfigureSintegra", None, _("Sintegra..."),
             group.get('config_sintegra')),
            ("ConfigurePlugins", None, _("Plugins...")),
            ("ConfigureUIForm", None, _("Forms...")),
            ("ConfigureTaxes", None, _("Taxes..."),
             group.get('config_taxes')),
            ("ConfigureSaleToken", None, _("Sale tokens...")),
            ("ConfigureParameters", None, _("Parameters..."),
             group.get('config_parameters')),
            ("NewUser", None, _("User..."), '',
             _("Create a new user")),
            ("StoqLinkConnect", None, _("Connect to Stoq.Link..."), '',
             _("Connect this Stoq installation to Stoq.Link")),
            ("ConfigureCertificates", None, _("Configure certificates...")),
        ]
        self.admin_ui = self.add_ui_actions(actions)
        self.set_help_section(_("Admin help"), 'app-admin')

    def create_ui(self):
        self.tasks = Tasks(self)
        self.tasks.set_model(self.model)
        self.tasks.add_defaults()
        self.model.set_sort_column_id(COL_LABEL, Gtk.SortType.ASCENDING)
        self.iconview.set_text_column(COL_LABEL)
        self.iconview.set_pixbuf_column(COL_PIXBUF)
        self.iconview.connect('item-activated', self.tasks.on_item_activated)
        self.iconview.select_path(self.model[0].path)

        # Connect releated actions and tasks and hide task if action is hidden
        for action_name, task in self.ACTION_TASKS.items():
            action = getattr(self, action_name)
            action.connect('activate', self._on_action__activate, task)
            if not action.get_enabled():
                self.tasks.hide_item(task)

    def activate(self, refresh=True):
        self.window.add_new_items([self.NewUser])
        self.window.add_search_items([
            self.SearchRole,
            self.SearchEmployee,
            self.SearchCfop,
            self.SearchFiscalBook,
            self.SearchUserProfile,
            self.SearchUser,
            self.SearchBranch,
            self.SearchComputer,
            self.SearchTaxTemplate,
            self.SearchEvents,
            self.SearchCostCenters,
            self.SearchDuplicatedPersons,
            self.SearchMessages,
        ])

        self.window.add_extra_items(
            [self.ConfigureDevices, self.ConfigurePaymentMethods,
             self.ConfigurePaymentCategories, self.ConfigureClientCategories,
             self.ConfigureTaxes, self.ConfigureSintegra,
             self.ConfigureParameters, self.ConfigureInvoices,
             self.ConfigureInvoicePrinters, self.ConfigureGridGroup,
             self.ConfigureGridAttribute, self.ConfigureUIForm,
             self.ConfigureSaleToken, self.ConfigureCertificates],
            _('Configure'))

        self.window.add_extra_items([self.ConfigurePlugins, self.StoqLinkConnect])

    def setup_focus(self):
        self.iconview.grab_focus()

    # Private

    def _new_user(self):
        store = api.new_store()
        model = run_person_role_dialog(UserEditor, self, store)
        store.confirm(model)
        store.close()
    #
    # Callbacks
    #

    def _on_action__activate(self, action, parameter, task):
        self.tasks.run_task(task)

    # New
    def on_NewUser__activate(self, action):
        self._new_user()

    # TODO: Create an task for this. I still need to find a proper metaphor
    # for the icon
    def on_SearchCostCenters__activate(self, action):
        self.run_dialog(CostCenterSearch, self.store)

    def on_SearchDuplicatedPersons__activate(self, action):
        self.run_dialog(PersonMergeDialog, self.store)

    def on_SearchMessages__activate(self, action):
        self.run_dialog(MessageSearch, self.store)
