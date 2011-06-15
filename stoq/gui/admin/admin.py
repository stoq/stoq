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
import pango
import gtk
from kiwi.enums import SearchFilterPosition
from kiwi.log import Logger
from kiwi.ui.objectlist import Column, SearchColumn
from kiwi.ui.search import ComboSearchFilter

from stoqlib.database.orm import AND
from stoqlib.database.runtime import (new_transaction, finish_transaction,
                                      get_current_branch)
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
from stoqlib.gui.help import show_contents, show_section
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

from stoq.gui.application import AppWindow, VersionChecker

_ = gettext.gettext

logger = Logger('stoq.gui.admin')

(COL_LABEL,
 COL_NAME,
 COL_PIXBUF) = range(3)

class Tasks(gtk.ScrolledWindow):
    def __init__(self, app):
        self.app = app
        gtk.ScrolledWindow.__init__(self)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.model = gtk.ListStore(str, str, gtk.gdk.Pixbuf)
        self.model.set_sort_column_id(COL_LABEL, gtk.SORT_ASCENDING)
        iconView = gtk.IconView(self.model)
        iconView.set_selection_mode(gtk.SELECTION_MULTIPLE)
        iconView.connect('item-activated', self.on_item_activated)
        iconView.set_text_column(COL_LABEL)
        iconView.set_pixbuf_column(COL_PIXBUF)
        iconView.set_item_padding(0)

        self.add(iconView)
        iconView.grab_focus()
        self.theme = gtk.icon_theme_get_default()

    def add_defaults(self):
        self.model.clear()
        items = [(_('Branches'), 'branches',
                  'gtk-home'),
                 (_('Client Categories'), 'client_categories',
                  'stoq-clients'),
                 (_('Clients'), 'clients',
                  'stoq-clients'),
                 (_('C.F.O.P'), 'cfop',
                  'calc'),
                 (_('Computers'), 'stations',
                  'system'),
                 (_('Devices'), 'devices',
                  'audio-card'),
                 (_('Employees'), 'employees',
                  'stoq-admin-app'),
                 (_('Roles'), 'employee_roles',
                  'stoq-users'),
                 (_('Fiscal Books'), 'fiscal_books',
                  'stoq-conference'),
                 (_('Invoice Printers'), 'invoice_printers',
                  'printer'),
                 (_('Payment Categories'), 'payment_categories',
                  'stoq-payable-app'),
                 (_('Payment Methods'), 'payment_methods',
                  'stoq-money'),
                 (_('Parameters'), 'parameters',
                  'gtk-preferences'),
                 (_('Plugins'), 'plugins',
                  'gtk-properties'),
                 (_('Taxes'), 'taxes',
                  'calc'),
                 (_('Suppliers'), 'suppliers',
                  'stoq-suppliers'),
                 (_('Transporters'), 'transporters',
                  'stoq-delivery'),
                 (_('Users'), 'users',
                  'stoq-hr'),
                 (_('User Profiles'), 'user_profiles',
                  'config-users'),
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
            except glib.GError, e:
                pixbuf = self.render_icon(pixbuf, gtk.ICON_SIZE_DIALOG)
        self.model.append([label, name, pixbuf])
        if cb is not None:
            setattr(self, '_open_' + name, cb)

    def on_item_activated(self, icon_view, path):
        name = self.model[path][COL_NAME]
        self.run_task(name)

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
        trans = new_transaction()
        model = self.app.run_dialog(ClientCategoryDialog, trans)
        finish_transaction(trans, model)
        trans.close()

    def _open_devices(self):
        self.app.run_dialog(DeviceSettingsDialog, self.app.conn)

    def _open_employees(self):
        self.app.run_dialog(EmployeeSearch, self.app.conn)

    def _open_employee_roles(self):
        self.app.run_dialog(EmployeeRoleSearch, self.app.conn)

    def _open_fiscal_books(self):
        self.app.run_dialog(FiscalBookEntrySearch, self.app.conn,
                            hide_footer=True)

    def _open_invoice_layouts(self):
        self.app.run_dialog(InvoiceLayoutDialog, self.app.conn)

    def _open_invoice_printers(self):
        if not InvoiceLayout.select(connection=self.app.conn):
            info(_(
                "You must create at least one invoice layout before adding an"
                "invoice printer"))
            return

        self.app.run_dialog(InvoicePrinterDialog, self.app.conn)

    def _open_payment_categories(self):
        trans = new_transaction()
        model = self.app.run_dialog(PaymentCategoryDialog, trans)
        finish_transaction(trans, model)
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
        branch = get_current_branch(self.app.conn)
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
    # FIXME: Remove
    klist_name = "foo"

    def __init__(self, app):
        # FIXME: Remove
        class x: pass
        self.foo = x()
        self.foo.get_columns = lambda : []
        self.foo.set_columns = lambda *x: None
        self.foo.set_selection_mode = lambda *x: None

        self.tasks = Tasks(self)
        self.tasks.add_defaults()
        AppWindow.__init__(self, app)

        self.search_holder.add(self.tasks)
        self.tasks.show_all()

        self._update_view()
        self._version_checker = VersionChecker(self.conn, self)
        self._version_checker.check_new_version()

    # FIXME: Remove
    def _update_view(self):
        pass
    def get_columns(self):
        return []

    #
    # Callbacks
    #

    def _on_fiscalbook_action_clicked(self, button):
        self.tasks.run_task('fiscal_books')

    def on_taxes__activate(self, action):
        self.tasks.run_task('taxes')

    def on_sintegra__activate(self, action):
        self.tasks.run_task('sintegra')

    def on_BranchSearch__activate(self, action):
        self.tasks.run_task('branches')

    def on_BranchStationSearch__activate(self, action):
        self.tasks.run_task('stations')

    def on_CfopSearch__activate(self, action):
        self.tasks.run_task('cfop')

    def on_EmployeeSearch__activate(self, action):
        self.tasks.run_task('employees')

    def on_UserSearch__activate(self, action):
        self.tasks.run_task('users')

    def on_EmployeeRole__activate(self, action):
        self.tasks.run_task('employee_roles')

    def on_UserProfile__activate(self, action):
        self.tasks.run_task('user_profiles')

    def on_about_menu__activate(self, action):
        self._run_about()

    def on_devices_setup__activate(self, action):
        self.tasks.run_task('devices')

    def on_system_parameters__activate(self, action):
        self.tasks.run_task('parameters')

    def on_invoice_printers__activate(self, action):
        self.tasks.run_task('invoice_printers')

    def on_invoices__activate(self, action):
        self.tasks.run_task('invoice_layouts')

    def on_PaymentMethod__activate(self, action):
        self.tasks.run_task('payment_methods')

    def on_payment_categories__activate(self, action):
        self.tasks.run_task('payment_categories')

    def on_client_categories__activate(self, action):
        self.tasks.run_task('client_categories')

    def on_Plugins__activate(self, action):
        self.tasks.run_task('plugins')

    def on_TaxTemplates__activate(self, action):
        self.tasks.run_task('tax_templates')

    def on_help_contents__activate(self, action):
        show_contents()

    def on_help_admin__activate(self, action):
        show_section('admin-inicial')
