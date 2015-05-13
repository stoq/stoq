# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015 Async Open Source <http://www.async.com.br>
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

import gtk
import mock

from stoq.gui.admin import AdminApp
from stoq.gui.test.baseguitest import BaseGUITest
from stoqlib.domain.uiform import UIField, UIForm
from stoqlib.gui.editors.formfieldeditor import FormFieldEditor
from stoqlib.lib.permissions import PermissionManager

from ..nfeui import NFeUI


__tests__ = 'plugins.nfe.nfeui.py'


class TestNfeUI(BaseGUITest):
    @classmethod
    def setUpClass(cls):
        cls.ui = NFeUI()
        BaseGUITest.setUpClass()

    @classmethod
    def tearDownClass(cls):
        """Undo what is done in the setup on NFeUI

        We must do this otherwise it will affect other tests
        """
        pm = PermissionManager.get_permission_manager()
        pm.set('InvoiceLayout', pm.PERM_ALL)
        pm.set('InvoicePrinter', pm.PERM_ALL)
        pm.set('app.sales.print_invoice', pm.PERM_ALL)

    def test_nfe_uiforms(self):
        app = self.create_app(AdminApp, u'admin')
        action = app.uimanager.get_action(
            '/ui/menubar/AppMenubarPH/ConfigureMenu/ConfigureUIForm')
        with mock.patch('stoq.gui.admin.AdminApp.run_dialog') as run_dialog:
            self.activate(action)
            args, kwargs = run_dialog.call_args
            editor = args[0]
            self.assertEquals(editor, FormFieldEditor)

    def test_uiform_editor(self):
        editor = FormFieldEditor(self.store)
        form = self.store.find(UIForm, form_name=u'employee').one()
        editor.forms.select(form)
        renderer_text = gtk.CellRendererText()
        renderer_toggle = gtk.CellRendererToggle()

        obj = self.store.find(UIField, field_name=u'street').any()
        # In order to test the following method, we must call it mannually,
        # otherwise the test wont call
        renderer = editor._uifield__cell_data_func(editor.forms, renderer_text,
                                                   obj, obj.description)
        self.assertEquals(renderer, obj.description)
        self.assertTrue(renderer_text.get_property('sensitive'))

        # Testing with NFe plugin inactive
        editor._uifield__cell_data_func(editor.forms,
                                        renderer_toggle,
                                        obj, obj.description)
        self.assertTrue(renderer_toggle.get_property('sensitive'))
        self.assertTrue(renderer_toggle.get_property('activatable'))

        # Testing with NFe plugin active
        path = 'stoqlib.gui.editors.formfieldeditor.get_plugin_manager'
        with mock.patch(path) as get_plugin_manager:
            get_plugin_manager.is_active.return_value = True
            editor._uifield__cell_data_func(editor.forms,
                                            renderer_toggle,
                                            obj, obj.description)
            self.assertFalse(renderer_toggle.get_property('sensitive'))
            self.assertFalse(renderer_toggle.get_property('activatable'))
