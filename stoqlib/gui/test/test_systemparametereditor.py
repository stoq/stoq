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
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.editors.parameterseditor import SystemParameterEditor


class TestSystemParameterEditor(GUITest):
    def test_create(self):
        parameter_data = self.create_parameter_data()
        editor = SystemParameterEditor(self.trans, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-show')

    def testConfirm(self):
        parameter_data = self.create_parameter_data()
        editor = SystemParameterEditor(self.trans, parameter_data)

        parameter_data.field_value = None
        self.assertFalse(editor.validate_confirm())
        self.assertFalse(editor.confirm())

        editor.model.field_value = '25'
        self.assertTrue(editor.confirm())
        self.check_editor(editor, 'editor-systemparameter-confirm',
                          [editor.retval])

    def test_entry(self):
        parameter_data = ParameterData.selectOneBy(self.trans,
                                                   field_name='CITY_SUGGESTED')
        editor = SystemParameterEditor(self.trans, parameter_data)
        editor._entry.update('any city')
        self.check_editor(editor, 'editor-systemparameter-entry')

    def test_combo_entry(self):
        parameter_data = ParameterData.selectOneBy(self.trans,
                                                   field_name='COUNTRY_SUGGESTED')
        editor = SystemParameterEditor(self.trans, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-combo-entry')

    def test_spin_entry(self):
        parameter_data = ParameterData.selectOneBy(self.trans,
                                                   field_name='MAX_SEARCH_RESULTS')
        editor = SystemParameterEditor(self.trans, parameter_data)
        editor._entry.update(456)
        self.check_editor(editor, 'editor-systemparameter-spin-entry')

    def test_text_view_entry(self):
        parameter_data = ParameterData.selectOneBy(self.trans,
                                                   field_name='NFE_FISCO_INFORMATION')
        editor = SystemParameterEditor(self.trans, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-text-view-entry')

    def test_image(self):
        parameter_data = ParameterData.selectOneBy(self.trans,
                                                   field_name='CUSTOM_LOGO_FOR_REPORTS')
        editor = SystemParameterEditor(self.trans, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-image')

    def test_radio(self):
        parameter_data = ParameterData.selectOneBy(self.trans,
                                                   field_name='DISABLE_COOKIES')
        editor = SystemParameterEditor(self.trans, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-radio')

    def test_options_combo(self):
        parameter_data = ParameterData.selectOneBy(self.trans,
                                                   field_name='NFE_DANFE_ORIENTATION')
        editor = SystemParameterEditor(self.trans, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-options-combo')

    def test_filechooser(self):
        parameter_data = ParameterData.selectOneBy(self.trans,
                                                   field_name='CAT52_DEST_DIR')
        editor = SystemParameterEditor(self.trans, parameter_data)
        self.check_editor(editor, 'editor-systemparameter-file-chooser')
