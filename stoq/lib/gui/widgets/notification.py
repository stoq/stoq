# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2018 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#


from gi.repository import Gtk

from stoq.lib.gui.base.gtkadds import replace_widget
from stoqlib.lib.translation import stoqlib_gettext
from stoq.lib.status import ResourceStatusManager

_ = stoqlib_gettext


class NotificationCounter(Gtk.Overlay):
    """Notification counter for widgets.

    This widget will wrap an existing widget and add a little red circle with a number
    inside it. Like a number of unread messages in an android app

    Note that the widget that will receive the notification must already be inside some
    container.
    """

    __gtype_name__ = 'NotificationCounter'

    def __init__(self, widget, count=0, blink=False):
        if isinstance(widget, Gtk.Button):
            # For buttons, put the notification *inside* the button, otherwise buttons
            # that are in a 'linked' box will be draw incorrectly.
            # Buttons have a style padding that must be removed so that the notification
            # appears as close to the border as possible.
            context = widget.get_style_context()
            padding = context.get_padding(Gtk.StateFlags.NORMAL)

            # But we must add that padding to the child (as margin), so that its not too
            # tight
            widget = widget.get_child()
            widget.props.margin_top = padding.top
            widget.props.margin_left = padding.left
            widget.props.margin_right = padding.right
            widget.props.margin_bottom = padding.bottom
            context.add_class('no-padding')

        super(NotificationCounter, self).__init__()
        replace_widget(widget, self)
        self.add(widget)

        label = Gtk.Label.new()
        label.get_style_context().add_class('warning_count')
        label.set_use_markup(True)
        if blink:
            label.get_style_context().add_class('blink')

        # Maybe add other positional options
        label.props.margin_top = 2
        label.props.margin_right = 2
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.START)

        self.add_overlay(label)
        self.set_overlay_pass_through(label, True)
        self.label = label
        self.show()

        self.set_count(count)
        self.status = ResourceStatusManager.get_instance()
        self.status.connect('status-changed', self._on__status_changed)

    def set_count(self, count):
        if count:
            self.label.set_markup('<small>%s</small>' % count)
            self.label.show()
        else:
            self.label.hide()

    def _on__status_changed(self, manager, status):
        count = len([r for r in manager.resources.values() if r.status > 1])
        self.set_count(count)
