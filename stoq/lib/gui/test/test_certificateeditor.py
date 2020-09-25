# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2017 Async Open Source <http://www.async.com.br>
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


from stoq.lib.gui.editors.certificateeditor import CertificateEditor
from stoq.lib.gui.test.uitestutils import GUITest


class TestCertificateEditor(GUITest):

    def test_create_certificate(self):
        editor = CertificateEditor(self.store)
        # In this state the dialog should not be confirmable
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])

        # FIXME: This is not working properly. Check on gtk 3
        # editor.certificate_chooser.set_filename('/bin/true')
        # # There apparently is a bug in pygtk that when a file is selected
        # # programatically, content-changed is emitted, but the
        # # widget.get_filename method is returning null. This is why we are
        # # calling the callback directly
        # editor.on_certificate_chooser__selection_changed(editor.certificate_chooser)
        # self.assertEqual(editor.model.name, 'true')

        editor.password.update('123456')
        # Now the dialog can be confirmed
        self.assertSensitive(editor.main_dialog, ['ok_button'])

        # self.assertTrue(editor.validate_confirm())
        self.check_editor(editor, 'editor-certificate-create')
