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


from stoqlib.gui.editors.parameterseditor import SystemParameterEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.parameters import sysparam, ParameterDetails


class TestSystemParameterEditor(GUITest):
    def test_create(self):
        parameter_data = self.create_parameter_data()
        detail = sysparam.get_detail_by_name(parameter_data.field_name)
        editor = SystemParameterEditor(self.store, detail)
        self.check_editor(editor, 'editor-systemparameter-show')

    def test_confirm(self):
        parameter_data = self.create_parameter_data()
        detail = sysparam.get_detail_by_name(parameter_data.field_name)
        editor = SystemParameterEditor(self.store, detail)

        parameter_data.field_value = None
        self.assertFalse(editor.validate_confirm())
        self.assertFalse(editor.confirm())

        editor.model.field_value = self.create_account().id
        self.assertTrue(editor.confirm())
        self.check_editor(editor, 'editor-systemparameter-confirm',
                          [editor.retval])

    def test_entry(self):
        detail = sysparam.get_detail_by_name(u'CITY_SUGGESTED')
        editor = SystemParameterEditor(self.store, detail)
        editor._entry.update('any city')
        self.check_editor(editor, 'editor-systemparameter-entry')

    def test_entry_insensitive(self):
        with self.sysparam(USER_HASH=u'45b27f4258024de58d2308753fcfff21'):
            detail = sysparam.get_detail_by_name(u'USER_HASH')
            editor = SystemParameterEditor(self.store, detail)
        self.check_editor(editor, 'editor-systemparameter-entry-insensitive')

    def test_combo_entry(self):
        detail = sysparam.get_detail_by_name(u'COUNTRY_SUGGESTED')
        editor = SystemParameterEditor(self.store, detail)
        self.check_editor(editor, 'editor-systemparameter-combo-entry')

    def test_spin_entry(self):
        detail = sysparam.get_detail_by_name(u'MAX_SEARCH_RESULTS')
        editor = SystemParameterEditor(self.store, detail)
        editor._entry.update(456)
        self.check_editor(editor, 'editor-systemparameter-spin-entry')

    def test_text_view_entry(self):
        detail = sysparam.get_detail_by_name(u'BOOKLET_INSTRUCTIONS')
        editor = SystemParameterEditor(self.store, detail)
        self.check_editor(editor, 'editor-systemparameter-text-view-entry')

    def test_unwrapped_text_view_entry(self):
        detail = ParameterDetails(u'FOO', 'section', 'short_desc', 'long_desc',
                                  unicode, multiline=True, initial=u'bar',
                                  wrap=False)
        sysparam.register_param(detail)
        editor = SystemParameterEditor(self.store, detail)
        self.check_editor(editor, 'editor-systemparameter-unwrapped-text-view-entry')
        sysparam._details.pop('FOO')

    def test_image(self):
        detail = sysparam.get_detail_by_name(u'CUSTOM_LOGO_FOR_REPORTS')
        editor = SystemParameterEditor(self.store, detail)
        self.check_editor(editor, 'editor-systemparameter-image')

    def test_radio(self):
        detail = sysparam.get_detail_by_name(u'DISABLE_COOKIES')
        editor = SystemParameterEditor(self.store, detail)
        self.check_editor(editor, 'editor-systemparameter-radio')

    def test_options_combo(self):
        detail = sysparam.get_detail_by_name(u'SCALE_BARCODE_FORMAT')
        editor = SystemParameterEditor(self.store, detail)
        self.check_editor(editor, 'editor-systemparameter-options-combo')

    def test_filechooser(self):
        detail = ParameterDetails(u'FOO', 'section', 'short_desc', 'long_desc',
                                  unicode, editor='directory-chooser')
        sysparam.register_param(detail)
        editor = SystemParameterEditor(self.store, detail)
        self.check_editor(editor, 'editor-systemparameter-file-chooser')
        sysparam._details.pop('FOO')
