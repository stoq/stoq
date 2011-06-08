# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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


(COL_PATH,
 COL_PIXBUF) = range(2)


class Tasks(gtk.ScrolledWindow):
    def __init__(self, app):
        self.app = app
        gtk.ScrolledWindow.__init__(self)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.model = gtk.ListStore(str, gtk.gdk.Pixbuf)
        self.model.set_sort_column_id(COL_PATH, gtk.SORT_ASCENDING)
        iconView = gtk.IconView(self.model)
        iconView.set_selection_mode(gtk.SELECTION_MULTIPLE)
        iconView.connect('item-activated', self.on_item_activated)
        iconView.set_text_column(COL_PATH)
        iconView.set_pixbuf_column(COL_PIXBUF)
        iconView.set_item_padding(0)

        self.add(iconView)
        iconView.grab_focus()
        self.theme = gtk.icon_theme_get_default()

    def add_defaults(self):
        self.model.clear()
        items = [(_('Branches'), 'gtk-home'),
                 (_('Client Categories'), 'stoq-clients'),
                 (_('Clients'), 'stoq-clients'),
                 (_('Cfop'), 'calc'),
                 (_('Devices'), 'audio-card'),
                 (_('Employee'), 'stoq-admin-app'),
                 (_('Employee Roles'), 'stoq-users'),
                 (_('FiscalBooks'), 'stoq-conference'),
                 (_('Invoice Printers'), 'printer'),
                 (_('Payment Categories'), 'stoq-payable-app'),
                 (_('Payment Methods'), 'stoq-money'),
                 (_('Parameters'), 'gtk-preferences'),
                 (_('Plugins'), 'gtk-properties'),
                 (_('Taxes'), 'calc'),
                 (_('Stations'), 'system'),
                 (_('Suppliers'), 'stoq-suppliers'),
                 (_('Transporters'), 'stoq-delivery'),
                 (_('Users'), 'stoq-hr'),
                 (_('User Profiles'), 'config-users'),
                 ]

        for item in items:
            if len(item) == 2:
                pixbuf = item[1]
                item = item[0]
            else:
                pixbuf = None
            self.add_item(item, pixbuf)

    def add_item(self, name, pixbuf=None, cb=None):
        if type(pixbuf) == str:
            try:
                pixbuf = self.theme.load_icon(pixbuf, 32, 0)
            except glib.GError, e:
                pixbuf = self.render_icon(pixbuf, gtk.ICON_SIZE_DIALOG)
        self.model.append([name, pixbuf])
        if cb is not None:
            setattr(self,
                    'open_' + name.replace(' ', '_'),
                    lambda : cb(None))

    def on_item_activated(self, icon_view, path):
        name = self.model[path][0].replace(' ', '_')

        func = getattr(self, 'open_%s' % name, None)
        if not func:
            return
        func()

    def open_Branches(self):
        self.app.run_dialog(BranchSearch, self.app.conn,
                            hide_footer=True)

    def open_Clients(self):
        self.app.run_dialog(ClientSearch, self.app.conn)

    def open_Client_Categories(self):
        trans = new_transaction()
        model = self.app.run_dialog(ClientCategoryDialog, trans)
        finish_transaction(trans, model)
        trans.close()

    def open_Devices(self):
        self.app.run_dialog(DeviceSettingsDialog, self.app.conn)

    def open_Employee_Roles(self):
        self.app.run_dialog(EmployeeRoleSearch, self.app.conn)

    def open_Employee(self):
        self.app.run_dialog(EmployeeSearch, self.app.conn)

    def open_FiscalBooks(self):
        self.app.run_dialog(FiscalBookEntrySearch, self.app.conn,
                            hide_footer=True)

    def open_Invoice_Printers(self):
        if not InvoiceLayout.select(connection=self.app.conn):
            info(_(
                "You must create at least one invoice layout before adding an"
                "invoice printer"))
            return

        self.app.run_dialog(InvoicePrinterDialog, self.app.conn)

    def open_Payment_Categories(self):
        trans = new_transaction()
        model = self.app.run_dialog(PaymentCategoryDialog, trans)
        finish_transaction(trans, model)
        trans.close()

    def open_Payment_Methods(self):
        self.app.run_dialog(PaymentMethodsDialog, self.app.conn)

    def open_Parameters(self):
        self.app.run_dialog(ParameterSearch, self.app.conn)

    def open_Plugins(self):
        self.app.run_dialog(PluginManagerDialog, self.app.conn)

    def open_Cfop(self):
        self.app.run_dialog(CfopSearch, self.app.conn, hide_footer=True)

    def open_Stations(self):
        self.app.run_dialog(StationSearch, self.app.conn, hide_footer=True)

    def open_Suppliers(self):
        self.app.run_dialog(SupplierSearch, self.app.conn)

    def open_Taxes(self):
        self.app.run_dialog(SellableTaxConstantsDialog, self.app.conn)

    def open_Transporters(self):
        self.app.run_dialog(TransporterSearch, self.app.conn)

    def open_Users(self):
        self.app.run_dialog(UserSearch, self.app.conn)

    def open_User_Profiles(self):
        self.app.run_dialog(UserProfileSearch, self.app.conn)


class AdminApp(AppWindow):

    app_name = _('Administrative')
    app_icon_name = 'stoq-admin-app'
    gladefile = "admin"
    klist_name = "foo"

    def __init__(self, app):
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

    def _update_view(self):
        pass
    def get_columns(self):
        return []

    #
    # Private
    #

    def _run_invoice_printer_dialog(self):
        if not InvoiceLayout.select(connection=self.conn):
            info(_(
                "You must create at least one invoice layout before adding an"
                "invoice printer"))
            return

        self.run_dialog(InvoicePrinterDialog, self.conn)

    def _run_payment_categories_dialog(self):
        trans = new_transaction()
        model = self.run_dialog(PaymentCategoryDialog, trans)
        finish_transaction(trans, model)
        trans.close()

    def _run_client_categories_dialog(self):
        trans = new_transaction()
        model = self.run_dialog(ClientCategoryDialog, trans)
        finish_transaction(trans, model)
        trans.close()

    #
    # Callbacks
    #

    def _on_fiscalbook_action_clicked(self, button):
        self.run_dialog(FiscalBookEntrySearch, self.conn, hide_footer=True)

    def on_taxes__activate(self, action):
        self.run_dialog(SellableTaxConstantsDialog, self.conn)

    def on_sintegra__activate(self, action):
        branch = get_current_branch(self.conn)

        if branch.manager is None:
            info(_(
                "You must define a manager to this branch before you can create"
                " a sintegra archive"))
            return

        self.run_dialog(SintegraDialog, self.conn)

    def on_BranchSearch__activate(self, action):
        self.run_dialog(BranchSearch, self.conn, hide_footer=True)

    def on_BranchStationSearch__activate(self, action):
        self.run_dialog(StationSearch, self.conn, hide_footer=True)

    def on_CfopSearch__activate(self, action):
        self.run_dialog(CfopSearch, self.conn, hide_footer=True)

    def on_EmployeeSearch__activate(self, action):
        self.run_dialog(EmployeeSearch, self.conn, hide_footer=True)

    def on_UserSearch__activate(self, action):
        self.run_dialog(UserSearch, self.conn)

    def on_EmployeeRole__activate(self, action):
        self.run_dialog(EmployeeRoleSearch, self.conn)

    def on_UserProfile__activate(self, action):
        self.run_dialog(UserProfileSearch, self.conn)

    def on_about_menu__activate(self, action):
        self._run_about()

    def on_devices_setup__activate(self, action):
        self.run_dialog(DeviceSettingsDialog, self.conn)

    def on_system_parameters__activate(self, action):
        self.run_dialog(ParameterSearch, self.conn)

    def on_invoice_printers__activate(self, action):
        self._run_invoice_printer_dialog()

    def on_invoices__activate(self, action):
        self.run_dialog(InvoiceLayoutDialog, self.conn)

    def on_PaymentMethod__activate(self, action):
        self.run_dialog(PaymentMethodsDialog, self.conn)

    def on_payment_categories__activate(self, action):
        self._run_payment_categories_dialog()

    def on_client_categories__activate(self, action):
        self._run_client_categories_dialog()

    def on_Plugins__activate(self, action):
        self.run_dialog(PluginManagerDialog, self.conn)

    def on_TaxTemplates__activate(self, action):
        self.run_dialog(TaxTemplatesSearch, self.conn)

    def on_help_contents__activate(self, action):
        show_contents()

    def on_help_admin__activate(self, action):
        show_section('admin-inicial')
