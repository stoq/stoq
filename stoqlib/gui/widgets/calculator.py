# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import decimal
import operator

import gtk
from kiwi.currency import currency
from kiwi.datatypes import converter, ValidationError
from kiwi.ui.widgets.entry import ProxyEntry
import pango

from stoqlib.gui.stockicons import STOQ_CALC
from stoqlib.lib.translation import stoqlib_gettext as _


class CalculatorPopup(gtk.Window):
    """A popup calculator for entries

    Right now it supports both
    :class:`kiwi.ui.widgets.spinbutton.ProxySpinButton` and
    :class:`kiwi.ui.widgets.entry.ProxyEntry`, as long as their
    data types are numeric (e.g. int, currency, Decimal, etc)
    """

    #: The add mode. Any value typed on the entry will be added to the
    #: original value. e.g. 10% means +10%
    MODE_ADD = 0

    #: The sub mode. Any value typed on the entry will be subtracted from the
    #: original value. e.g. 10% means -10%
    MODE_SUB = 1

    _mode = None
    _data_type_mapper = {
        'currency': currency,
        'Decimal': decimal.Decimal,
    }

    def __init__(self, entry, mode):
        """
        :param entry: a :class:`kiwi.ui.widgets.spinbutton.ProxySpinButton`
            or a :class:`kiwi.ui.widgets.entry.ProxyEntry` subclass
        :param mode: one of :attr:`.MODE_ADD`, :attr:`.MODE_SUB`
        """
        self._mode = mode

        self._new_value = None
        self._popped_entry = entry
        self._data_type = self._data_type_mapper[entry.data_type]
        self._converter = converter.get_converter(self._data_type)

        gtk.Window.__init__(self, gtk.WINDOW_POPUP)

        self._create_ui()

    #
    # Public API
    #

    def popup(self):
        if not self._popped_entry.get_realized():
            return

        if not self._update_ui():
            return

        toplevel = self._popped_entry.get_toplevel().get_toplevel()
        if (isinstance(toplevel, (gtk.Window, gtk.Dialog)) and
            toplevel.get_group()):
            toplevel.get_group().add_window(self)

        # width is meant for the popup window
        x, y, width, height = self._get_position()
        self.set_size_request(width, -1)
        self.move(x, y)
        self.show_all()

        if not self._popup_grab_window():
            self.hide()
            return

        self.grab_add()

    def popdown(self):
        if not self._popped_entry.get_realized():
            return

        self.grab_remove()
        self.hide()
        self._popped_entry.grab_focus()

    #
    #  Private
    #

    def _create_ui(self):
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.KEY_PRESS_MASK)
        self.connect('key-press-event', self._on__key_press_event)
        self.connect('button-press-event', self._on__button_press_event)

        # This is done on entry to check where to put the validation/mandatory
        # icons. We should put the calculator on the other side.
        # Note that spinbuttons are always right aligned and thus
        # xalign will always be 1.0
        if self._popped_entry.get_property('xalign') > 0.5:
            self._icon_pos = 'secondary-icon'
        else:
            self._icon_pos = 'primary-icon'

        self._popped_entry.set_property(self._icon_pos + '-activatable', True)
        self._popped_entry.set_property(self._icon_pos + '-tooltip-text',
                                        _("Do calculations on top of this value"))
        self._popped_entry.connect('notify::sensitive',
                                   self._on_popped_entry_sensitive__notify)
        self._popped_entry.connect('icon-press',
                                   self._on_popped_entry__icon_press)
        self._toggle_calculator_icon()

        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        self.add(frame)
        frame.show()

        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(6, 6, 2, 2)
        frame.add(alignment)
        alignment.show()

        vbox = gtk.VBox(spacing=6)
        alignment.add(vbox)
        vbox.show()

        self._main_label = gtk.Label()
        self._main_label.set_ellipsize(pango.ELLIPSIZE_END)
        vbox.pack_start(self._main_label, True, True)
        self._main_label.show()

        self._entry = ProxyEntry()
        # FIXME: We need a model_attribute here or else the entry.is_valid()
        # will always return None. Check proxywidget.py's FIXME to see why
        self._entry.model_attribute = 'not_used'
        self._entry.connect('validate', self._on_entry__validate)
        self._entry.connect_after('changed', self._after_entry__changed)
        self._entry.set_alignment(1.0)
        vbox.pack_start(self._entry, True, True)
        self._entry.show()

        hbox = gtk.HBox(spacing=6)
        vbox.pack_start(hbox, True, True)
        hbox.show()

        self._label = gtk.Label()
        self._label.set_property('xalign', 1.0)
        self._label.set_use_markup(True)
        hbox.pack_start(self._label, True, True)
        self._label.show()

        self._warning = gtk.Image()
        hbox.pack_start(self._warning, False, False)

        self.set_resizable(False)
        self.set_screen(self._popped_entry.get_screen())

    def _update_ui(self):
        try:
            self._new_value = self._data_type(self._popped_entry.get_text())
        except decimal.InvalidOperation:
            return False

        self._entry.set_text('')
        self._entry.set_tooltip_text(_("Use absolute or percentage (%) value"))
        self._preview_new_value()
        self._main_label.set_text(self._get_main_label())

        return True

    def _get_main_label(self):
        if self._mode == self.MODE_ADD:
            return (_("Surcharge") if self._data_type == currency else
                    _("Addition"))
        elif self._mode == self.MODE_SUB:
            return (_("Discount") if self._data_type == currency else
                    _("Subtraction"))
        else:
            raise AssertionError

    def _set_warning(self, warning):
        if warning is None:
            self._warning.hide()
        else:
            self._warning.set_from_stock(gtk.STOCK_DIALOG_WARNING,
                                         gtk.ICON_SIZE_MENU)
            self._warning.set_tooltip_text(warning)
            self._warning.show()

    def _popup_grab_window(self):
        activate_time = 0L
        window = self.get_window()
        grab_status = gtk.gdk.pointer_grab(window, True,
                                           (gtk.gdk.BUTTON_PRESS_MASK |
                                            gtk.gdk.BUTTON_RELEASE_MASK |
                                            gtk.gdk.POINTER_MOTION_MASK),
                                           None, None, activate_time)
        if grab_status == gtk.gdk.GRAB_SUCCESS:
            if gtk.gdk.keyboard_grab(window, True, activate_time) == 0:
                return True
            else:
                window.get_display().pointer_ungrab(activate_time)
                return False

        return False

    def _get_position(self):
        widget = self._popped_entry

        allocation = widget.get_allocation()
        window = widget.get_window()

        if hasattr(window, 'get_root_coords'):
            x = 0
            y = 0
            if not widget.get_has_window():
                x += allocation.x
                y += allocation.y
            x, y = window.get_root_coords(x, y)
        else:
            # PyGTK lacks gdk_window_get_root_coords(),
            # but we can use get_origin() instead, which is the
            # same thing in our case.
            x, y = widget.window.get_origin()

        return x, y + allocation.height, allocation.width, allocation.height

    def _get_new_value(self):
        operation = self._entry.get_text().strip()
        operation = operation.replace(',', '.')

        if operation.endswith('%'):
            op_value = operation[:-1]
            percentage = True
        else:
            op_value = operation
            percentage = False

        if not operation:
            return

        if operation[0] in ['+', '-']:
            raise ValueError(_("Operator signals are not supported..."))

        if self._mode == self.MODE_SUB:
            op = operator.sub
        elif self._mode == self.MODE_ADD:
            op = operator.add

        try:
            op_value = decimal.Decimal(op_value)
        except decimal.InvalidOperation:
            raise ValueError(
                _("'%s' is not a valid operation...") % (operation,))

        if percentage:
            value = op(self._new_value, self._new_value * (op_value / 100))
        else:
            value = op(self._new_value, op_value)

        return value

    def _update_new_value(self):
        if not self._entry.is_valid():
            return

        self._new_value = self._get_new_value()
        self._entry.set_text('')
        self._preview_new_value()

    def _preview_new_value(self):
        self._label.set_markup('<b>%s</b>' % (
            self._converter.as_string(self._new_value), ))

    def _maybe_apply_new_value(self):
        if self._entry.get_text():
            self._update_new_value()
            return

        self._popped_entry.update(self._new_value)

        self.popdown()

    def _toggle_calculator_icon(self):
        if self._popped_entry.get_sensitive():
            pixbuf = self.render_icon(STOQ_CALC, gtk.ICON_SIZE_MENU)
        else:
            pixbuf = None

        self._popped_entry.set_property(self._icon_pos + '-pixbuf', pixbuf)

    #
    #  Callbacks
    #

    def _on__key_press_event(self, window, event):
        keyval = event.keyval
        if keyval == gtk.keysyms.Escape:
            self.popdown()
            return True
        elif keyval in [gtk.keysyms.Return,
                        gtk.keysyms.KP_Enter,
                        gtk.keysyms.Tab]:
            self._maybe_apply_new_value()
            return True

        return False

    def _on__button_press_event(self, window, event):
        # If we're clicking outside of the window
        # close the popup
        if (event.window != self.get_window() or
            (tuple(self.allocation.intersect(
                   gtk.gdk.Rectangle(x=int(event.x), y=int(event.y),
                                     width=1, height=1)))) == (0, 0, 0, 0)):
            self.popdown()

    def _on_entry__validate(self, entry, value):
        try:
            value = self._get_new_value()
        except ValueError as err:
            return ValidationError('%s\n%s' % (err,
                                   _("Use absolute or percentage (%) value")))

        if value:
            warning = self._popped_entry.emit('validate', value)
            warning = warning and str(warning)
        else:
            warning = None

        self._set_warning(warning)

    def _after_entry__changed(self, entry):
        entry.validate(force=True)

    def _on_popped_entry_sensitive__notify(self, obj, pspec):
        self._toggle_calculator_icon()

    def _on_popped_entry__icon_press(self, entry, icon_pos, event):
        if icon_pos != gtk.ENTRY_ICON_SECONDARY:
            return

        self.popup()
