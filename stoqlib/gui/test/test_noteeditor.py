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

from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestNoteEditor(GUITest):
    def test_show(self):
        person = self.create_person()
        editor = NoteEditor(self.store, person, 'notes', label_text='Notes')
        self.check_editor(editor, 'editor-note-show')

    def test_confirm_with_payment_comment(self):
        comment = self.create_payment_comment(u'foo')
        self.assertEquals(comment.comment, u'foo')
        editor = NoteEditor(self.store, comment, 'comment', label_text='Notes')
        editor.notes.update('bar')
        self.click(editor.main_dialog.ok_button)
        self.assertEquals(comment.comment, u'bar')

    def test_cancel_with_non_domain(self):
        class TempNote(object):
            obs = u'bin'

        obj = TempNote()
        self.assertEquals(obj.obs, u'bin')
        editor = NoteEditor(self.store, obj, 'obs', label_text='Notes')
        editor.notes.update('foo')

        # Cancelling the dialog should manually revert the changes (since the
        # object edited is not a domain object)
        self.click(editor.main_dialog.cancel_button)
        self.assertEquals(obj.obs, u'bin')

    def test_button_label(self):
        sale = self.create_sale()
        sale_comment = self.create_sale_comment(sale, u'teste')
        sale.status = sale.STATUS_QUOTE
        editor = NoteEditor(self.store, sale_comment, attr_name='comment',
                            ok_button_label=u"Cancel sale",
                            cancel_button_label=u"Don't cancel")
        cancel_sale_button = editor.main_dialog.ok_button.get_label()
        not_cancel_button = editor.main_dialog.cancel_button.get_label()
        self.assertEquals(cancel_sale_button, u"Cancel sale")
        self.assertEquals(not_cancel_button, u"Don't cancel")
