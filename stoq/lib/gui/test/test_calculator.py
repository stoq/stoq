# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoq/lib/gui/widgets/calculator.py'

import contextlib

from gi.repository import Gtk, Gdk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.widgets.spinbutton import ProxySpinButton
import mock

from stoq.lib.gui.stockicons import STOQ_CALC
from stoq.lib.gui.test.uitestutils import GUITest
from stoq.lib.gui.widgets.calculator import CalculatorPopup


class TestCalculatorPopup(GUITest):
    def test_show(self):
        spinbutton = ProxySpinButton()
        spinbutton.data_type = currency
        calc = CalculatorPopup(spinbutton, CalculatorPopup.MODE_SUB)

        self.check_widget(calc, 'calculator-popup-show')

    def test_attach(self):
        entry = ProxyEntry()
        entry.data_type = currency
        self.assertEqual(entry.get_property('secondary-icon-pixbuf'), None)
        theme = Gtk.IconTheme.get_default()

        CalculatorPopup(entry, CalculatorPopup.MODE_SUB)
        pixbuf_pixels = theme.load_icon(STOQ_CALC, Gtk.IconSize.MENU, 0).get_pixels()

        self.assertEqual(
            entry.get_property('secondary-icon-pixbuf').get_pixels(), pixbuf_pixels)
        entry.set_sensitive(False)
        self.assertEqual(entry.get_property('secondary-icon-pixbuf'), None)
        entry.set_sensitive(True)
        self.assertEqual(
            entry.get_property('secondary-icon-pixbuf').get_pixels(), pixbuf_pixels)

        spinbutton = ProxySpinButton()
        spinbutton.data_type = currency
        self.assertEqual(spinbutton.get_property('secondary-icon-pixbuf'), None)

        CalculatorPopup(spinbutton, CalculatorPopup.MODE_SUB)
        self.assertEqual(
            spinbutton.get_property('secondary-icon-pixbuf').get_pixels(), pixbuf_pixels)
        spinbutton.set_sensitive(False)
        self.assertEqual(spinbutton.get_property('secondary-icon-pixbuf'), None)
        spinbutton.set_sensitive(True)
        self.assertEqual(
            spinbutton.get_property('secondary-icon-pixbuf').get_pixels(), pixbuf_pixels)

    def test_popup(self):
        entry = ProxyEntry()
        entry.data_type = currency
        entry.set_text('150')
        calc = CalculatorPopup(entry, CalculatorPopup.MODE_SUB)

        event = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
        event.window = Gdk.get_default_root_window()

        with mock.patch.object(calc, 'popup') as popup:
            entry.emit('icon-press', Gtk.EntryIconPosition.PRIMARY, event)
            self.assertEqual(popup.call_count, 0)
            entry.emit('icon-press', Gtk.EntryIconPosition.SECONDARY, event)
            self.assertEqual(popup.call_count, 1)

    def test_popdown(self):
        entry = ProxyEntry()
        entry.data_type = currency
        entry.set_text('150')
        calc = CalculatorPopup(entry, CalculatorPopup.MODE_SUB)

        with contextlib.nested(
                mock.patch.object(calc, '_maybe_apply_new_value'),
                mock.patch.object(calc, 'popdown')) as (manv, popdown):
            # Those keys should try to apply the value
            for keyval in [Gdk.KEY_Return,
                           Gdk.KEY_KP_Enter,
                           Gdk.KEY_Tab]:
                event = Gdk.Event.new(Gdk.EventType.KEY_PRESS)
                event.keyval = keyval
                event.window = Gdk.get_default_root_window()
                calc.emit('key-press-event', event)

                self.assertEqual(manv.call_count, 1)
                self.assertEqual(popdown.call_count, 0)

                manv.reset_mock()
                popdown.reset_mock()

            event = Gdk.Event.new(Gdk.EventType.KEY_PRESS)
            # Escape should popdown the popup
            event.keyval = Gdk.KEY_Escape
            event.window = Gdk.get_default_root_window()
            calc.emit('key-press-event', event)

            self.assertEqual(popdown.call_count, 1)
            self.assertEqual(manv.call_count, 0)
            manv.reset_mock()
            popdown.reset_mock()

            event = Gdk.Event.new(Gdk.EventType.KEY_PRESS)
            # Any other should not do anything
            event.keyval = Gdk.KEY_A
            event.window = Gdk.get_default_root_window()
            calc.emit('key-press-event', event)

            self.assertEqual(manv.call_count, 0)
            self.assertEqual(popdown.call_count, 0)

    def test_apply(self):
        entry = ProxyEntry()
        entry.data_type = currency
        entry.set_text('150')
        calc = CalculatorPopup(entry, CalculatorPopup.MODE_SUB)

        # calc.popup will not work here, so call validate_popup directly
        calc.validate_popup()
        calc._entry.set_text('10%')
        event = Gdk.Event.new(Gdk.EventType.KEY_PRESS)
        event.keyval = Gdk.KEY_Return
        event.window = Gdk.get_default_root_window()
        calc.emit('key-press-event', event)
        calc.emit('key-press-event', event)
        self.assertEqual(entry.read(), 135)

    def test_validate(self):
        def validate_entry(entry, value):
            if value == 100:
                return ValidationError()

        # FIXME: For some reason, entry is not emitting 'changed' event
        # on set_text, not even if we call entry.emit('changed') by hand.
        # That only happens here on the test. Figure out why
        def update_entry(entry, value):
            entry.set_text(value)
            entry.validate(force=True)

        entry = ProxyEntry()
        entry.data_type = currency
        entry.connect('validate', validate_entry)
        entry.set_text('150')

        calc = CalculatorPopup(entry, CalculatorPopup.MODE_SUB)
        # calc.popup will not work here, so call validate_popup directly
        calc.validate_popup()
        self.assertValid(calc, ['_entry'])
        self.assertNotVisible(calc, ['_warning'])

        for value in ['abc', '+10%', '-10%', '+10', '-10']:
            update_entry(calc._entry, value)
            self.assertInvalid(calc, ['_entry'])
            self.assertNotVisible(calc, ['_warning'])

        update_entry(calc._entry, '40')
        self.assertValid(calc, ['_entry'])
        self.assertNotVisible(calc, ['_warning'])

        # 50 of discount will make the value invalid on entry
        # (see validate_entry above)
        update_entry(calc._entry, '50')
        self.assertValid(calc, ['_entry'])
        self.assertVisible(calc, ['_warning'])
