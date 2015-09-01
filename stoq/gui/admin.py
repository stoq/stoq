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

import glib
import gtk

from stoqlib.api import api
from stoqlib.domain.invoice import InvoiceLayout
from stoqlib.gui.dialogs.clientcategorydialog import ClientCategoryDialog
from stoqlib.gui.dialogs.devices import DeviceSettingsDialog
from stoqlib.gui.editors.formfieldeditor import FormFieldEditor
from stoqlib.gui.dialogs.invoicedialog import (InvoiceLayoutDialog,
                                               InvoicePrinterDialog)
from stoqlib.gui.dialogs.paymentcategorydialog import PaymentCategoryDialog
from stoqlib.gui.dialogs.paymentmethod import PaymentMethodsDialog
from stoqlib.gui.dialogs.personmergedialog import PersonMergeDialog
from stoqlib.gui.dialogs.pluginsdialog import PluginManagerDialog
from stoqlib.gui.dialogs.sellabledialog import SellableTaxConstantsDialog
from stoqlib.gui.dialogs.sintegradialog import SintegraDialog
from stoqlib.gui.editors.personeditor import UserEditor
from stoqlib.gui.search.costcentersearch import CostCenterSearch
from stoqlib.gui.search.eventsearch import EventSearch
from stoqlib.gui.search.fiscalsearch import CfopSearch, FiscalBookEntrySearch
from stoqlib.gui.search.parametersearch import ParameterSearch
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.gridsearch import (GridGroupSearch,
                                           GridAttributeSearch)
from stoqlib.gui.search.personsearch import (ClientSearch,
                                             EmployeeRoleSearch,
                                             EmployeeSearch,
                                             BranchSearch,
                                             SupplierSearch,
                                             TransporterSearch,
                                             UserSearch)
from stoqlib.gui.search.profilesearch import UserProfileSearch
from stoqlib.gui.search.stationsearch import StationSearch
from stoqlib.gui.search.salesearch import SaleTokenSearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.search.taxclasssearch import TaxTemplatesSearch
from stoqlib.gui.stockicons import (
    STOQ_CALC, STOQ_ADMIN_APP, STOQ_CLIENTS, STOQ_DEVICES, STOQ_DELIVERY,
    STOQ_DOCUMENTS, STOQ_EDIT, STOQ_FORMS, STOQ_HR, STOQ_MONEY,
    STOQ_PAYABLE_APP, STOQ_PLUGIN, STOQ_SUPPLIERS, STOQ_SYSTEM, STOQ_TAXES,
    STOQ_USER_PROFILES, STOQ_USERS, STOQ_PRODUCTS, STOQ_SERVICES)
from stoqlib.gui.utils.keybindings import get_accels
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.decorators import public
from stoqlib.lib.message import info
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.translation import locale_sorted, stoqlib_gettext

from stoq.gui.shell.shellapp import ShellApp

_ = stoqlib_gettext

logger = logging.getLogger(__name__)

(COL_LABEL,
 COL_NAME,
 COL_PIXBUF) = range(3)


class Tasks(object):
    def __init__(self, app):
        self.app = app

        self.theme = gtk.icon_theme_get_default()

    def set_model(self, model):
        self.model = model
        self.model.clear()

    def add_defaults(self):
        items = [
            (_('Branches'), 'branches', gtk.STOCK_HOME),
            (_('C.F.O.P.'), 'cfop', STOQ_CALC),
            (_('Client Categories'), 'client_categories', STOQ_CLIENTS),
            (_('Clients'), 'clients', STOQ_CLIENTS),
            (_('Computers'), 'stations', STOQ_SYSTEM),
            (_('Devices'), 'devices', STOQ_DEVICES),
            (_('Employees'), 'employees', STOQ_ADMIN_APP),
            (_('Events'), 'events', gtk.STOCK_DIALOG_WARNING),
            (_('Fiscal Books'), 'fiscal_books', STOQ_EDIT),
            (_('Forms'), 'forms', STOQ_FORMS),
            (_('Invoice Printers'), 'invoice_printers', gtk.STOCK_PRINT),
            (_('Parameters'), 'parameters', gtk.STOCK_PREFERENCES),
            (_('Payment Categories'), 'payment_categories', STOQ_PAYABLE_APP),
            (_('Payment Methods'), 'payment_methods', STOQ_MONEY),
            (_('Plugins'), 'plugins', STOQ_PLUGIN),
            (_('Products'), 'products', STOQ_PRODUCTS),
            (_('Roles'), 'employee_roles', STOQ_USERS),
            (_('Services'), 'services', STOQ_SERVICES),
            (_('Taxes'), 'taxes', STOQ_TAXES),
            (_('Suppliers'), 'suppliers', STOQ_SUPPLIERS),
            (_('Tax Classes'), 'tax_templates', STOQ_DOCUMENTS),
            (_('Transporters'), 'transporters', STOQ_DELIVERY),
            (_('User Profiles'), 'user_profiles', STOQ_USER_PROFILES),
            (_('Users'), 'users', STOQ_HR),
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
        if type(pixbuf) == str:
            stock_id = pixbuf
            try:
                pixbuf = self.theme.load_icon(pixbuf, 32, 0)
            except glib.GError:
                pixbuf = self.app.get_toplevel().render_icon(pixbuf, gtk.ICON_SIZE_DIALOG)
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
        ]
        self.admin_ui = self.add_ui_actions('', actions,
                                            filename='admin.xml')
        self.set_help_section(_("Admin help"), 'app-admin')

    def create_ui(self):
        self.tasks = Tasks(self)
        self.tasks.set_model(self.model)
        self.tasks.add_defaults()
        self.model.set_sort_column_id(COL_LABEL, gtk.SORT_ASCENDING)
        self.iconview.set_text_column(COL_LABEL)
        self.iconview.set_pixbuf_column(COL_PIXBUF)
        self.iconview.connect('item-activated', self.tasks.on_item_activated)
        self.iconview.select_path(self.model[0].path)

        # Connect releated actions and tasks and hide task if action is hidden
        for action_name, task in self.ACTION_TASKS.items():
            action = getattr(self, action_name)
            action.connect('activate', self._on_action__activate, task)
            if not action.get_visible():
                self.tasks.hide_item(task)

    def activate(self, refresh=True):
        # Admin app doesn't have anything to print/export
        for widget in [self.window.Print,
                       self.window.ExportSpreadSheet]:
            widget.set_visible(False)

        self.window.add_new_items([self.NewUser])
        self.window.add_search_items([self.SearchUser,
                                      self.SearchEmployee])
        self.window.NewToolItem.set_tooltip(
            _("Create a new user"))
        self.window.SearchToolItem.set_tooltip(
            _("Search for users"))

    def deactivate(self):
        self.uimanager.remove_ui(self.admin_ui)

    def setup_focus(self):
        self.iconview.grab_focus()

    def new_activate(self):
        self._new_user()

    def search_activate(self):
        self.tasks.run_task('users')

    # Private

    def _new_user(self):
        store = api.new_store()
        model = run_person_role_dialog(UserEditor, self, store)
        store.confirm(model)
        store.close()
    #
    # Callbacks
    #

    def _on_action__activate(self, action, task):
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
