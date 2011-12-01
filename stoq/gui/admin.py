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
from stoqlib.gui.dialogs.paymentcategorydialog import PaymentCategoryDialog
from stoqlib.gui.dialogs.paymentmethod import PaymentMethodsDialog
from stoqlib.gui.dialogs.pluginsdialog import PluginManagerDialog
from stoqlib.gui.dialogs.sintegradialog import SintegraDialog
from stoqlib.gui.editors.invoiceeditor import (InvoiceLayoutDialog,
                                               InvoicePrinterDialog)
from stoqlib.gui.editors.personeditor import UserEditor
from stoqlib.gui.editors.sellableeditor import SellableTaxConstantsDialog
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
        items = [(_('Branches'), 'branches',
                  'gtk-home'),
                 (_('Client Categories'), 'client_categories',
                  'stoq-clients'),
                 (_('Clients'), 'clients',
                  'stoq-clients'),
                 (_('C.F.O.P.'), 'cfop',
                  'stoq-calc'),
                 (_('Computers'), 'stations',
                  'stoq-system'),
                 (_('Devices'), 'devices',
                  'stoq-devices'),
                 (_('Employees'), 'employees',
                  'stoq-admin-app'),
                 (_('Events'), 'events',
                  'gtk-dialog-warning'),
                 (_('Roles'), 'employee_roles',
                  'stoq-users'),
                 (_('Fiscal Books'), 'fiscal_books',
                  'stoq-edit'),
                 (_('Invoice Printers'), 'invoice_printers',
                  'gtk-print'),
                 (_('Payment Categories'), 'payment_categories',
                  'stoq-payable-app'),
                 (_('Payment Methods'), 'payment_methods',
                  'stoq-money'),
                 (_('Parameters'), 'parameters',
                  'gtk-preferences'),
                 (_('Plugins'), 'plugins',
                  'gtk-properties'),
                 (_('Taxes'), 'taxes',
                  'stoq-taxes'),
                 (_('Suppliers'), 'suppliers',
                  'stoq-suppliers'),
                 (_('Transporters'), 'transporters',
                  'stoq-delivery'),
                 (_('Users'), 'users',
                  'stoq-hr'),
                 (_('User Profiles'), 'user_profiles',
                  'stoq-user-profiles'),
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
    app_icon_name = 'stoq-admin-app'
    gladefile = "admin"
    embedded = True

    #
    # Application
    #

    def create_actions(self):
        actions = [
            ('menubar', None, ''),
            # Admin
            ("AdminMenu", None, _("_Admin")),

            # Search
            ("SearchRole", None, _("Roles..."), '<Control><Alt>o'),
            ("SearchEmployee", None, _("Employees..."), '<Control><Alt>e'),
            ("SearchEvents", None, _("Events..."), ''),
            ("SearchCfop", None, _("C.F.O.P..."), '<Control>o'),
            ("SearchFiscalBook", None, _("Fiscal books..."), '<Control><Alt>f'),
            ("SearchUserProfile", None, _("Profiles..."), '<Control><Alt>u'),
            ("SearchUser", None, _("Users..."), '<Control>u'),
            ("SearchBranch", None, _("Branches..."), '<Control>b'),
            ("SearchComputer", None, _('Computers...'), '<Control><Alt>h'),
            ("SearchTaxTemplate", None, _('Tax Classes...')),

            # Configure
            ("ConfigureMenu", None, _("_Configure")),
            ("ConfigureDevices", None, _("Devices..."), '<Control>d'),
            ("ConfigurePaymentMethods", None, _("Payment methods..."),
             '<Control>m'),
            ("ConfigurePaymentCategories", None, _("Payment categories..."),
             '<Control>a'),
            ("ConfigureClientCategories", None, _("Client categories..."),
             '<control>x'),
            ("ConfigureInvoices", None, _("Invoices..."), '<Control>n'),
            ("ConfigureInvoicePrinters", None, _("Invoice printers..."),
             '<Control>f'),
            ("ConfigureSintegra", None, _("Sintegra..."), '<Control>w'),
            ("ConfigurePlugins", None, _("Plugins...")),
            ("ConfigureTaxes", None, _("Taxes..."), '<Control>l'),
            ("ConfigureParameters", None, _("Parameters..."), '<Control>y'),

            # New
            ("NewUser", None, _("User"), '',
             _("Create a new user")),
            ]
        self.admin_ui = self.add_ui_actions('', actions,
                                            filename='admin.xml')
        self.set_help_section(_("Admin help"), 'admin-inicial')

    def create_ui(self):
        self.tasks = Tasks(self)
        self.tasks.set_model(self.model)
        self.tasks.add_defaults()
        self.model.set_sort_column_id(COL_LABEL, gtk.SORT_ASCENDING)
        self.iconview.set_text_column(COL_LABEL)
        self.iconview.set_pixbuf_column(COL_PIXBUF)
        self.iconview.connect('item-activated', self.tasks.on_item_activated)
        self.iconview.select_path(self.model[0].path)

    def activate(self):
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
