# -*- Mode: Python; coding: iso-8859-1 -*-
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

import gettext

import glib
import gtk
from kiwi.log import Logger

from stoqlib.api import api
from stoqlib.domain.invoice import InvoiceLayout
from stoqlib.gui.dialogs.clientcategorydialog import ClientCategoryDialog
from stoqlib.gui.dialogs.devices import DeviceSettingsDialog
from stoqlib.gui.editors.formfieldeditor import FormFieldEditor
from stoqlib.gui.dialogs.paymentcategorydialog import PaymentCategoryDialog
from stoqlib.gui.dialogs.paymentmethod import PaymentMethodsDialog
from stoqlib.gui.dialogs.pluginsdialog import PluginManagerDialog
from stoqlib.gui.dialogs.sintegradialog import SintegraDialog
from stoqlib.gui.editors.invoiceeditor import (InvoiceLayoutDialog,
                                               InvoicePrinterDialog)
from stoqlib.gui.editors.personeditor import UserEditor
from stoqlib.gui.editors.sellableeditor import SellableTaxConstantsDialog
from stoqlib.gui.editors.shortcutseditor import ShortcutsEditor
from stoqlib.gui.keybindings import get_accels
from stoqlib.gui.search.eventsearch import EventSearch
from stoqlib.gui.search.fiscalsearch import CfopSearch, FiscalBookEntrySearch
from stoqlib.gui.search.parametersearch import ParameterSearch
from stoqlib.gui.search.personsearch import (ClientSearch,
                                             EmployeeRoleSearch,
                                             EmployeeSearch,
                                             BranchSearch,
                                             SupplierSearch,
                                             TransporterSearch,
                                             UserSearch)
from stoqlib.gui.search.profilesearch import UserProfileSearch
from stoqlib.gui.search.stationsearch import StationSearch
from stoqlib.gui.search.taxclasssearch import TaxTemplatesSearch
from stoqlib.gui.stockicons import (
    STOQ_CALC, STOQ_ADMIN_APP, STOQ_CLIENTS, STOQ_DEVICES, STOQ_DELIVERY,
    STOQ_DOCUMENTS, STOQ_EDIT, STOQ_FORMS, STOQ_KEYBOARD, STOQ_HR, STOQ_MONEY,
    STOQ_PAYABLE_APP, STOQ_SUPPLIERS, STOQ_SYSTEM, STOQ_TAXES,
    STOQ_USER_PROFILES, STOQ_USERS)
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.message import info

from stoq.gui.application import AppWindow

_ = gettext.gettext

logger = Logger('stoq.gui.admin')

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
            (_('Client Categories'), 'client_categories', STOQ_CLIENTS),
            (_('Clients'), 'clients', STOQ_CLIENTS),
            (_('C.F.O.P.'), 'cfop', STOQ_CALC),
            (_('Computers'), 'stations', STOQ_SYSTEM),
            (_('Devices'), 'devices', STOQ_DEVICES),
            (_('Employees'), 'employees', STOQ_ADMIN_APP),
            (_('Events'), 'events', gtk.STOCK_DIALOG_WARNING),
            (_('Roles'), 'employee_roles', STOQ_USERS),
            (_('Fiscal Books'), 'fiscal_books', STOQ_EDIT),
            (_('Invoice Printers'), 'invoice_printers', gtk.STOCK_PRINT),
            (_('Keyboard shortcuts'), 'keyboard_shortcuts', STOQ_KEYBOARD),
            (_('Forms'), 'forms', STOQ_FORMS),
            (_('Payment Categories'), 'payment_categories', STOQ_PAYABLE_APP),
            (_('Payment Methods'), 'payment_methods', STOQ_MONEY),
            (_('Parameters'), 'parameters', gtk.STOCK_PREFERENCES),
            (_('Plugins'), 'plugins', gtk.STOCK_PROPERTIES),
            (_('Taxes'), 'taxes', STOQ_TAXES),
            (_('Tax Classes'), 'tax_templates', STOQ_DOCUMENTS),
            (_('Suppliers'), 'suppliers', STOQ_SUPPLIERS),
            (_('Transporters'), 'transporters', STOQ_DELIVERY),
            (_('Users'), 'users', STOQ_HR),
            (_('User Profiles'), 'user_profiles', STOQ_USER_PROFILES),
            ]

        for label, name, pixbuf in items:
            self.add_item(label, name, pixbuf)

    def add_item(self, label, name, pixbuf=None, cb=None):
        """
        @param label: Label to show in the interface
        @param name: Name to use to store internally and use by callbacks
        @param pixbuf: a pixbuf or stock-id/icon-name for the item
        @param cb: callback
        """
        if type(pixbuf) == str:
            try:
                pixbuf = self.theme.load_icon(pixbuf, 32, 0)
            except glib.GError:
                pixbuf = self.app.get_toplevel().render_icon(pixbuf, gtk.ICON_SIZE_DIALOG)
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
        self.app.run_dialog(BranchSearch, self.app.conn,
                            hide_footer=True)

    def _open_clients(self):
        self.app.run_dialog(ClientSearch, self.app.conn)

    def _open_client_categories(self):
        trans = api.new_transaction()
        model = self.app.run_dialog(ClientCategoryDialog, trans)
        api.finish_transaction(trans, model)
        trans.close()

    def _open_devices(self):
        self.app.run_dialog(DeviceSettingsDialog, self.app.conn)

    def _open_employees(self):
        self.app.run_dialog(EmployeeSearch, self.app.conn)

    def _open_employee_roles(self):
        self.app.run_dialog(EmployeeRoleSearch, self.app.conn)

    def _open_events(self):
        self.app.run_dialog(EventSearch, self.app.conn,
                            hide_toolbar=True)

    def _open_forms(self):
        self.app.run_dialog(FormFieldEditor, self.app.conn)

    def _open_fiscal_books(self):
        self.app.run_dialog(FiscalBookEntrySearch, self.app.conn,
                            hide_footer=True)

    def _open_invoice_layouts(self):
        self.app.run_dialog(InvoiceLayoutDialog, self.app.conn)

    def _open_invoice_printers(self):
        if not InvoiceLayout.select(connection=self.app.conn):
            info(_("You must create at least one invoice layout "
                   "before adding an invoice printer"))
            return

        self.app.run_dialog(InvoicePrinterDialog, self.app.conn)

    def _open_payment_categories(self):
        trans = api.new_transaction()
        model = self.app.run_dialog(PaymentCategoryDialog, trans)
        api.finish_transaction(trans, model)
        trans.close()

    def _open_payment_methods(self):
        self.app.run_dialog(PaymentMethodsDialog, self.app.conn)

    def _open_parameters(self):
        self.app.run_dialog(ParameterSearch, self.app.conn)

    def _open_plugins(self):
        self.app.run_dialog(PluginManagerDialog, self.app.conn)

    def _open_cfop(self):
        self.app.run_dialog(CfopSearch, self.app.conn, hide_footer=True)

    def _open_keyboard_shortcuts(self):
        self.app.run_dialog(ShortcutsEditor, self.app.conn)

    def _open_sintegra(self):
        branch = api.get_current_branch(self.app.conn)
        if branch.manager is None:
            info(_(
                "You must define a manager to this branch before you can create"
                " a sintegra archive"))
            return

        self.app.run_dialog(SintegraDialog, self.app.conn)

    def _open_stations(self):
        self.app.run_dialog(StationSearch, self.app.conn, hide_footer=True)

    def _open_suppliers(self):
        self.app.run_dialog(SupplierSearch, self.app.conn)

    def _open_taxes(self):
        self.app.run_dialog(SellableTaxConstantsDialog, self.app.conn)

    def _open_tax_templates(self):
        self.app.run_dialog(TaxTemplatesSearch, self.app.conn)

    def _open_transporters(self):
        self.app.run_dialog(TransporterSearch, self.app.conn)

    def _open_users(self):
        self.app.run_dialog(UserSearch, self.app.conn)

    def _open_user_profiles(self):
        self.app.run_dialog(UserProfileSearch, self.app.conn)


class AdminApp(AppWindow):

    app_name = _('Administrative')
    gladefile = "admin"
    embedded = True

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
            ("ConfigureTaxes", None, _("Taxes..."),
             group.get('config_taxes')),
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

    def activate(self, params):
        # Admin app doesn't have anything to print/export
        for widget in (self.app.launcher.Print, self.app.launcher.ExportCSV):
            widget.set_visible(False)

        self.app.launcher.add_new_items([self.NewUser])
        self.app.launcher.add_search_items([self.SearchUser,
                                            self.SearchEmployee])
        self.app.launcher.NewToolItem.set_tooltip(
            _("Create a new user"))
        self.app.launcher.SearchToolItem.set_tooltip(
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
        trans = api.new_transaction()
        model = run_person_role_dialog(UserEditor, self, trans)
        api.finish_transaction(trans, model)
    #
    # Callbacks
    #

    # Search

    def on_SearchRole__activate(self, action):
        self.tasks.run_task('employee_roles')

    def on_SearchEmployee__activate(self, action):
        self.tasks.run_task('employees')

    def on_SearchFiscalBook__activate(self, button):
        self.tasks.run_task('fiscal_books')

    def on_SearchCfop__activate(self, action):
        self.tasks.run_task('cfop')

    def on_SearchUserProfile__activate(self, action):
        self.tasks.run_task('user_profiles')

    def on_SearchUser__activate(self, action):
        self.tasks.run_task('users')

    def on_SearchBranch__activate(self, action):
        self.tasks.run_task('branches')

    def on_SearchComputer__activate(self, action):
        self.tasks.run_task('stations')

    def on_SearchTaxTemplate__activate(self, action):
        self.tasks.run_task('tax_templates')

    def on_SearchEvents__activate(self, action):
        self.tasks.run_task('events')

    # Configure

    def on_ConfigureDevices__activate(self, action):
        self.tasks.run_task('devices')

    def on_ConfigurePaymentMethods__activate(self, action):
        self.tasks.run_task('payment_methods')

    def on_ConfigurePaymentCategories__activate(self, action):
        self.tasks.run_task('payment_categories')

    def on_ConfigureClientCategories__activate(self, action):
        self.tasks.run_task('client_categories')

    def on_ConfigureTaxes__activate(self, action):
        self.tasks.run_task('taxes')

    def on_ConfigureSintegra__activate(self, action):
        self.tasks.run_task('sintegra')

    def on_ConfigureParameters__activate(self, action):
        self.tasks.run_task('parameters')

    def on_ConfigureInvoices__activate(self, action):
        self.tasks.run_task('invoice_layouts')

    def on_ConfigureInvoicePrinters__activate(self, action):
        self.tasks.run_task('invoice_printers')

    def on_ConfigurePlugins__activate(self, action):
        self.tasks.run_task('plugins')

    # New
    def on_NewUser__activate(self, action):
        self._new_user()
