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


from stoqlib.domain.parameter import ParameterData
from stoqlib.gui.editors.parameterseditor import SystemParameterEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestSystemParameterEditor(GUITest):
    def test_create(self):
        parameter_data = self.create_parameter_data()
        editor = SystemParameterEditor(self.store, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-show')

    def test_confirm(self):
        parameter_data = self.create_parameter_data()
        editor = SystemParameterEditor(self.store, parameter_data)

        parameter_data.field_value = None
        self.assertFalse(editor.validate_confirm())
        self.assertFalse(editor.confirm())

        editor.model.field_value = self.create_account().id
        self.assertTrue(editor.confirm())
        self.check_editor(editor, 'editor-systemparameter-confirm',
                          [editor.retval])

    def test_entry(self):
        parameter_data = self.store.find(ParameterData,
                                         field_name=u'CITY_SUGGESTED').one()
        editor = SystemParameterEditor(self.store, parameter_data)
        editor._entry.update('any city')
        self.check_editor(editor, 'editor-systemparameter-entry')

    def test_entry_insensitive(self):
        with self.sysparam(USER_HASH=u'45b27f4258024de58d2308753fcfff21'):
            parameter_data = self.store.find(ParameterData,
                                             field_name=u'USER_HASH').one()
            editor = SystemParameterEditor(self.store, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-entry-insensitive')

    def test_combo_entry(self):
        parameter_data = self.store.find(ParameterData,
                                         field_name=u'COUNTRY_SUGGESTED').one()
        editor = SystemParameterEditor(self.store, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-combo-entry')

    def test_spin_entry(self):
        parameter_data = self.store.find(ParameterData,
                                         field_name=u'MAX_SEARCH_RESULTS').one()
        editor = SystemParameterEditor(self.store, parameter_data)
        editor._entry.update(456)
        self.check_editor(editor, 'editor-systemparameter-spin-entry')

    def test_text_view_entry(self):
        parameter_data = self.store.find(ParameterData,
                                         field_name=u'NFE_FISCO_INFORMATION').one()
        editor = SystemParameterEditor(self.store, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-text-view-entry')

    def test_unwrapped_text_view_entry(self):
        parameter_data = self.store.find(ParameterData,
                                         field_name=u'ADDITIONAL_INFORMATION_ON_COUPON').one()
        editor = SystemParameterEditor(self.store, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-unwrapped-text-view-entry')

    def test_image(self):
        parameter_data = self.store.find(ParameterData,
                                         field_name=u'CUSTOM_LOGO_FOR_REPORTS').one()
        editor = SystemParameterEditor(self.store, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-image')

    def test_radio(self):
        parameter_data = self.store.find(ParameterData,
                                         field_name=u'DISABLE_COOKIES').one()
        editor = SystemParameterEditor(self.store, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-radio')

    def test_options_combo(self):
        parameter_data = self.store.find(ParameterData,
                                         field_name=u'NFE_DANFE_ORIENTATION').one()
        editor = SystemParameterEditor(self.store, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-options-combo')

    def test_filechooser(self):
        parameter_data = self.store.find(ParameterData,
                                         field_name=u'CAT52_DEST_DIR').one()
        editor = SystemParameterEditor(self.store, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-file-chooser')
