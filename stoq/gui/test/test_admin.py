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
from stoqlib.database.runtime import StoqlibStore
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
        search, store = args
        self.assertEquals(search, search_dialog)
        self.assertTrue(isinstance(store, StoqlibStore))

    @mock.patch('stoq.gui.admin.AdminApp.run_dialog')
    def _check_dialog_task(self, app, task_name, dialog, run_dialog):
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self._activate_task(app, task_name)
                run_dialog.assert_called_once_with(dialog, self.store)

    def testInitial(self):
        app = self.create_app(AdminApp, u'admin')
        self.check_app(app, u'admin')

    @mock.patch('stoq.gui.admin.api.new_store')
    @mock.patch('stoq.gui.admin.run_person_role_dialog')
    def test_new_user(self, run_dialog, new_store):
        new_store.return_value = self.store

        app = self.create_app(AdminApp, u'admin')

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.main_window.NewUser)
                run_dialog.assert_called_once_with(UserEditor, app.main_window,
                                                   self.store)

    @mock.patch('stoq.gui.admin.api.new_store')
    def test_open_dialogs(self, new_store):
        new_store.return_value = self.store

        app = self.create_app(AdminApp, u'admin')

        self._check_search_task(app, u'branches', BranchSearch)
        self._check_search_task(app, u'cfop', CfopSearch)
        self._check_dialog_task(app, u'client_categories', ClientCategoryDialog)
        self._check_search_task(app, u'clients', ClientSearch)
        self._check_search_task(app, u'devices', DeviceSettingsDialog)
        self._check_search_task(app, u'employees', EmployeeSearch)
        self._check_search_task(app, u'employee_roles', EmployeeRoleSearch)
        self._check_search_task(app, u'events', EventSearch)
        self._check_dialog_task(app, u'forms', FormFieldEditor)
        self._check_search_task(app, u'fiscal_books', FiscalBookEntrySearch)
        self._check_dialog_task(app, u'invoice_printers', InvoicePrinterDialog)
        self._check_dialog_task(app, u'payment_categories', PaymentCategoryDialog)
        self._check_dialog_task(app, u'payment_methods', PaymentMethodsDialog)
        self._check_dialog_task(app, u'parameters', ParameterSearch)
        self._check_dialog_task(app, u'plugins', PluginManagerDialog)
        self._check_search_task(app, u'stations', StationSearch)
        self._check_search_task(app, u'suppliers', SupplierSearch)
        self._check_search_task(app, u'tax_templates', TaxTemplatesSearch)
        self._check_search_task(app, u'taxes', SellableTaxConstantsDialog)
        self._check_search_task(app, u'transporters', TransporterSearch)
        self._check_search_task(app, u'users', UserSearch)
        self._check_search_task(app, u'user_profiles', UserProfileSearch)

        # adding the invoice_layouts to the the item list (because it
        # isn't included there by default)
        app.main_window.tasks.add_item(u'foo', u'invoice_layouts', None)

        self._check_dialog_task(app, u'invoice_layouts', InvoiceLayoutDialog)

    @mock.patch('stoq.gui.admin.info')
    def test_sintegra_dialog(self, info):
        app = self.create_app(AdminApp, u'admin')

        # adding the sintegra to the the item list (because it
        # isn't included there by default)
        app.main_window.tasks.add_item(u'bar', u'sintegra', None)

        self._activate_task(app, u'sintegra')
        info.assert_called_once_with(u'You must define a manager to this branch '
                                     u'before you can create a sintegra archive')

        branch = api.get_current_branch(self.store)
        branch.manager = self.create_employee()

        self._check_search_task(app, u'sintegra', SintegraDialog)

    def test_hide_item(self):
        app = self.create_app(AdminApp, u'admin')

        app.main_window.tasks.hide_item(u'branches')
        tasks = [(row[1]) for row in app.main_window.tasks.model]
        self.assertFalse(u'branches' in tasks)
