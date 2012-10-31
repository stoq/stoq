# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

import mock

from stoq.gui.admin import AdminApp
from stoq.gui.test.baseguitest import BaseGUITest
from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.gui.dialogs.clientcategorydialog import ClientCategoryDialog
from stoqlib.gui.dialogs.devices import DeviceSettingsDialog
from stoqlib.gui.editors.formfieldeditor import FormFieldEditor
from stoqlib.gui.dialogs.invoicedialog import (InvoiceLayoutDialog,
                                               InvoicePrinterDialog)
from stoqlib.gui.dialogs.paymentcategorydialog import PaymentCategoryDialog
from stoqlib.gui.dialogs.paymentmethod import PaymentMethodsDialog
from stoqlib.gui.dialogs.pluginsdialog import PluginManagerDialog
from stoqlib.gui.editors.personeditor import UserEditor
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


class TestAdmin(BaseGUITest):
    def _check_search_task(self, app, task_name, search_dialog, run_dialog):
        app.main_window.tasks.run_task(task_name)
        run_dialog.assert_called_once()
        args, kwargs = run_dialog.call_args
        search, trans = args
        self.assertEquals(search, search_dialog)
        self.assertTrue(isinstance(trans, StoqlibTransaction))

    def _check_dialog_task(self, app, task_name, dialog, run_dialog):
        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                app.main_window.tasks.run_task(task_name)
                run_dialog.assert_called_once()
                args, kwargs = run_dialog.call_args
                dialog, trans = args
                self.assertEquals(dialog, dialog)
                self.assertEquals(trans, self.trans)

    def testInitial(self):
        app = self.create_app(AdminApp, 'admin')
        self.check_app(app, 'admin')

    @mock.patch('stoq.gui.admin.api.new_transaction')
    @mock.patch('stoq.gui.admin.run_person_role_dialog')
    def test_new_user(self, run_dialog, new_transaction):
        new_transaction.return_value = self.trans

        app = self.create_app(AdminApp, 'admin')

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.NewUser)
                run_dialog.assert_called_once_with(UserEditor, app.main_window,
                                                   self.trans)

    @mock.patch('stoq.gui.admin.api.new_transaction')
    @mock.patch('stoq.gui.admin.AdminApp.run_dialog')
    def test_open_dialogs(self, run_dialog, new_transaction):
        new_transaction.return_value = self.trans

        app = self.create_app(AdminApp, 'admin')

        self._check_search_task(app, 'branches', BranchSearch, run_dialog)
        self._check_search_task(app, 'cfop', CfopSearch, run_dialog)
        self._check_dialog_task(app, 'client_categories', ClientCategoryDialog,
                                run_dialog)
        self._check_search_task(app, 'clients', ClientSearch, run_dialog)
        self._check_search_task(app, 'devices', DeviceSettingsDialog, run_dialog)
        self._check_search_task(app, 'employees', EmployeeSearch, run_dialog)
        self._check_search_task(app, 'employee_roles', EmployeeRoleSearch, run_dialog)
        self._check_search_task(app, 'events', EventSearch, run_dialog)
        self._check_dialog_task(app, 'forms', FormFieldEditor, run_dialog)
        self._check_search_task(app, 'fiscal_books', FiscalBookEntrySearch,
                                run_dialog)
        self._check_dialog_task(app, 'invoice_printers', InvoicePrinterDialog,
                                run_dialog)
        self._check_dialog_task(app, 'invoice_layouts', InvoiceLayoutDialog,
                                run_dialog)
        self._check_dialog_task(app, 'payment_categories', PaymentCategoryDialog,
                                run_dialog)
        self._check_dialog_task(app, 'payment_methods', PaymentMethodsDialog,
                                run_dialog)
        self._check_dialog_task(app, 'parameters', ParameterSearch, run_dialog)
        self._check_dialog_task(app, 'plugins', PluginManagerDialog, run_dialog)
        self._check_search_task(app, 'stations', StationSearch, run_dialog)
        self._check_search_task(app, 'suppliers', SupplierSearch, run_dialog)
        self._check_search_task(app, 'tax_templates', TaxTemplatesSearch,
                                run_dialog)
        self._check_search_task(app, 'transporters', TransporterSearch,
                                run_dialog)
        self._check_search_task(app, 'users', UserSearch, run_dialog)
        self._check_search_task(app, 'user_profiles', UserProfileSearch,
                                run_dialog)
