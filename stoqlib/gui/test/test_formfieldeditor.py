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

from stoqlib.database.runtime import new_store
from stoqlib.domain.uiform import UIField, UIForm
from stoqlib.gui.editors.formfieldeditor import FormFieldEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestFormFieldEditor(GUITest):
    def test_show(self):
        dialog = FormFieldEditor(self.store)
        self.check_dialog(dialog, 'dialog-formfield-show')

    @mock.patch('stoqlib.gui.editors.formfieldeditor.info')
    def test_set_not_mandatory(self, info):
        store = self.store
        store2 = new_store()
        store3 = new_store()

        client_form = store.find(UIForm, form_name=u'client').one()
        field = store.find(UIField,
                           ui_form=client_form, field_name=u'name').one()
        self.assertEquals(field.mandatory, True)

        field2 = store2.find(UIField,
                             ui_form=client_form, field_name=u'name').one()

        dialog = FormFieldEditor(self.store)
        dialog.forms.select(client_form)
        self.assertEquals(list(dialog.fields.get_cell_contents())[7][2], True)
        setattr(field, 'mandatory', False)
        dialog.fields.refresh()
        self.assertEquals(list(dialog.fields.get_cell_contents())[7][2], False)
        self.assertEquals(field2.mandatory, True)
        dialog.confirm()

        field3 = store3.find(UIField,
                             ui_form=client_form, field_name=u'name').one()
        self.assertEquals(field3.mandatory, False)

        store2.close()
        store3.close()

        # Restore initial state of the test database.
        setattr(field, 'mandatory', True)
        store.commit()
