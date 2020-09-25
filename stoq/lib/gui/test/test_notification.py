# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2018 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoq/lib/gui/widgets/notification.py'

from gi.repository import Gtk
#import mock

from stoq.lib.gui.test.uitestutils import GUITest
from stoq.lib.gui.widgets.notification import NotificationCounter


class TestNotificationCounter(GUITest):
    def test_show_label(self):
        box = Gtk.Box()
        label = Gtk.Label('Teste')

        box.pack_start(Gtk.Label('label before'), False, False, 0)
        box.pack_start(label, False, False, 0)
        box.pack_start(Gtk.Label('label after'), False, False, 0)
        self.check_widget(box, 'notification-before-add')

        self.assertEqual(label.get_parent(), box)
        counter = NotificationCounter(label)
        self.assertEqual(label.get_parent(), counter)

        counter.set_count(10)
        self.check_widget(box, 'notification-after-add')

    def test_show_button(self):
        box = Gtk.Box()
        button = Gtk.Button('Teste')
        box.pack_start(button, False, False, 0)

        self.assertEqual(button.get_parent(), box)
        counter = NotificationCounter(button)

        # Buttons are not reparented...
        self.assertEqual(button.get_parent(), box)

        # ... The notification is added inside them
        self.assertEqual(button.get_child(), counter)
