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


from stoqlib.gui.editors.invoiceeditor import InvoiceLayoutEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestInvoiceLayoutEditor(GUITest):
    def test_create(self):
        editor = InvoiceLayoutEditor(self.store)
        self.check_editor(editor, 'editor-invoicelayout-create')

    def test_select_free_text(self):
        layout = self.create_invoice_layout()
        field = self.create_invoice_field(field_name=u'FREE_TEXT',
                                          layout=layout, content=u'free text')
        field2 = self.create_invoice_field(field_name=u'CLIENT_NAME', layout=layout)
        editor = InvoiceLayoutEditor(self.store, model=layout)
        field_info = editor.grid.add_field(field.field_name, u'FREE_TEXT',
                                           0, 0, 10, 1, field)
        field_info2 = editor.grid.add_field(field2.field_name, u'CLIENT_NAME',
                                            0, 1, 10, 1, field2)

        # Testing selecting the client_name widget
        editor.grid.select_field(field_info2)
        self.assertNotSensitive(editor, ['text'])
        self.assertEquals(editor.text.read(), u'')

        # Selecting a free text widget
        editor.grid.select_field(field_info)
        self.assertEquals(editor.text.read(), u'free text')
        # We have to do this to emmit __changed signal
        editor.text.insert_text(u'new ')
        self.assertEquals(editor.text.read(), u'new free text')

        ## Testing clicking on the grid but not on a widget
        editor.grid.select_field(None)
        self.assertNotSensitive(editor, ['text'])
        self.assertEquals(editor.text.read(), u'')
        self.assertEquals(editor.field_name.read(), u'')
