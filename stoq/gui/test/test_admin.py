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
from stoqlib.api import api
from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.gui.dialogs.clientcategorydialog import ClientCategoryDialog
from stoqlib.gui.dialogs.devices import DeviceSettingsDialog
from stoqlib.gui.editors.formfieldeditor import FormFieldEditor
from stoqlib.gui.dialogs.invoicedialog import (InvoiceLayoutDialog,
                                               InvoicePrinterDialog)
from stoqlib.gui.dialogs.paymentcategorydialog import PaymentCategoryDialog
from stoqlib.gui.dialogs.paymentmethod import PaymentMethodsDialog
from stoqlib.gui.dialogs.pluginsdialog import PluginManagerDialog
from stoqlib.gui.dialogs.sellabledialog import SellableTaxConstantsDialog
from stoqlib.gui.dialogs.sintegradialog import SintegraDialog
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
    def _activate_task(self, app, task_name):
        for row in app.main_window.iconview.get_model():
            if row[1] == task_name:
                app.main_window.iconview.item_activated(row.path)
                break

    @mock.patch('stoq.gui.admin.AdminApp.run_dialog')
    def _check_search_task(self, app, task_name, search_dialog, run_dialog):
        self._activate_task(app, task_name)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        search, trans = args
        self.assertEquals(search, search_dialog)
        self.assertTrue(isinstance(trans, StoqlibTransaction))

    @mock.patch('stoq.gui.admin.AdminApp.run_dialog')
    def _check_dialog_task(self, app, task_name, dialog, run_dialog):
        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self._activate_task(app, task_name)
                run_dialog.assert_called_once_with(dialog, self.trans)

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
    def test_open_dialogs(self, new_transaction):
        new_transaction.return_value = self.trans

        app = self.create_app(AdminApp, 'admin')

        self._check_search_task(app, 'branches', BranchSearch)
        self._check_search_task(app, 'cfop', CfopSearch)
        self._check_dialog_task(app, 'client_categories', ClientCategoryDialog)
        self._check_search_task(app, 'clients', ClientSearch)
        self._check_search_task(app, 'devices', DeviceSettingsDialog)
        self._check_search_task(app, 'employees', EmployeeSearch)
        self._check_search_task(app, 'employee_roles', EmployeeRoleSearch)
        self._check_search_task(app, 'events', EventSearch)
        self._check_dialog_task(app, 'forms', FormFieldEditor)
        self._check_search_task(app, 'fiscal_books', FiscalBookEntrySearch)
        self._check_dialog_task(app, 'invoice_printers', InvoicePrinterDialog)
        self._check_dialog_task(app, 'payment_categories', PaymentCategoryDialog)
        self._check_dialog_task(app, 'payment_methods', PaymentMethodsDialog)
        self._check_dialog_task(app, 'parameters', ParameterSearch)
        self._check_dialog_task(app, 'plugins', PluginManagerDialog)
        self._check_search_task(app, 'stations', StationSearch)
        self._check_search_task(app, 'suppliers', SupplierSearch)
        self._check_search_task(app, 'tax_templates', TaxTemplatesSearch)
        self._check_search_task(app, 'taxes', SellableTaxConstantsDialog)
        self._check_search_task(app, 'transporters', TransporterSearch)
        self._check_search_task(app, 'users', UserSearch)
        self._check_search_task(app, 'user_profiles', UserProfileSearch)

        # adding the invoice_layouts to the the item list (because it
        # isn't included there by default)
        app.main_window.tasks.add_item('foo', 'invoice_layouts', None)

        self._check_dialog_task(app, 'invoice_layouts', InvoiceLayoutDialog)

    @mock.patch('stoq.gui.admin.info')
    def test_sintegra_dialog(self, info):
        app = self.create_app(AdminApp, 'admin')

        # adding the sintegra to the the item list (because it
        # isn't included there by default)
        app.main_window.tasks.add_item('bar', 'sintegra', None)

        self._activate_task(app, 'sintegra')
        info.assert_called_once_with('You must define a manager to this branch '
                                     'before you can create a sintegra archive')

        branch = api.get_current_branch(self.trans)
        branch.manager = self.create_employee()

        self._check_search_task(app, 'sintegra', SintegraDialog)

    def test_hide_item(self):
        app = self.create_app(AdminApp, 'admin')

        app.main_window.tasks.hide_item('branches')
        tasks = [(row[1]) for row in app.main_window.tasks.model]
        self.assertFalse('branches' in tasks)
