# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import gtk

from kiwi.utils import gsignal

class _response_data:
   response_id = None

def get_response_data(widget, create):
    ad = widget.get_data('pygtk-info-bar-response')
    if ad is None and create:
        ad = _response_data()
        widget.set_data('pygtk-info-bar-response', ad)

    return ad


def get_response_for_widget(widget):
    rd = get_response_data(widget, False)
    if not rd:
        return gtk.RESPONSE_NONE
    else:
        return rd.response_id


class InfoBar(gtk.HBox):
    gsignal('response', int)
    type_detail = ["infobar-info",
                   "infobar-warning",
                   "infobar-question",
                   "infobar-error",
                   "infobar"]

    def __init__(self, message_type=None):
        gtk.HBox.__init__(self)
        self.message_type = message_type
        self._create_ui()

    def _create_ui(self):
        self._content_area = gtk.HBox(False, 0)
        self._content_area.show()
        self.pack_start(content_area, True, True, 0)
        self._content_area.set_spacing(16)
        self._content_area.set_border_width(8)

        self._action_area = gtk.VButtonBox()
        self._action_area.show()
        self._action_area.set_layout(gtk.BUTTONBOX_END)
        self._action_area.set_spacing(6)
        self._action_area.set_border_width(5)

        self.pack_start(self._action_area, False, True, 0)

        self.set_app_paintable(True)
        self.set_redraw_on_allocate(True)

    def do_expose_event(widget, event):
        if self.message_type != gtk.MESSAGE_OTHER:
            detail = self.type_detail[self.message_type]

            self.style.paint_box(self.window, gtk.STATE_NORMAL,
                    gtk.SHADOW_OUT, None, widget, detail,
                    widget.allocation.x,
                    widget.allocation.y,
                    widget.allocation.width,
                    widget.allocation.height)

        self.chain(widget, event)
        return False

    def update_colors(self):
        fg_color_name = ["info_fg_color", "warning_fg_color",
                         "question_fg_color", "error_fg_color",
                         "other_fg_color"]
        bg_color_name = ["info_bg_color", "warning_bg_color",
                         "question_bg_color", "error_bg_color",
                         "other_bg_color"]

        style = widget.get_style()
        fg = style.lookup_color(fg_color_name[self._message_type])
        bg = style.lookup_color(bg_color_name[self._message_type])
        if fg is None or bg is None:
            if self._message_type == gtk.MESSAGE_INFO:
                fg = gtk.gdk.Color(0xb800, 0xad00, 0x9d00)
                bg = gtk.gdk.Color(0xff00, 0xff00, 0xbf00)
            elif self._message_type == gtk.MESSAGE_WARNING:
                fg = gtk.gdk.Color(0xb000, 0x7a00, 0x2b00)
                bg = gtk.gdk.Color(0xfc00, 0xaf00, 0x3e00)
            elif self._message_type == gtk.MESSAGE_QUESTION:
                fg = gtk.gdk.Color(0x6200, 0x7b00, 0xd960)
                bg = gtk.gdk.Color(0x8c00, 0xb000, 0xd700)
            elif self._message_type == gtk.MESSAGE_ERROR:
                fg = gtk.gdk.Color(0xa800, 0x2700, 0x2700)
                bg = gtk.gdk.Color(0xf000, 0x3800, 0x3800)
            elif self._message_type == gtk.MESSAGE_OTHER:
                fg = gtk.gdk.Color(0xb800, 0xad00, 0x9d00)
                bg = gtk.gdk.Color(0xff00, 0xff00, 0xbf00)

        if not bg.equal(widget.style[gtk.STATE_NORMAL]):
            self.modify_bg(gtk.STATE_NORMAL, bg)

        if not fg.equal(widget.style[gtk.STATE_NORMAL]):
            self.modify_bg(gtk.STATE_NORMAL, fg)

    def add_action_widget(child, response_id):
        ad = get_response_data(child, True);
        ad.response_id = response_id

        if isinstance(child, gtk.Button):
            def activated(*unused):
                response_id = get_response_for_widget(button)
                self.response(button, response_id)
            button.connect('clicked', action_widget_activated)

        self._action_area.pack_end(child, False, False, 0)
        if response_id == gtk.RESPONSE_HELP:
            self._action_area.set_child_secondary(child, True)

    def add_button(self, button_text, response_id):
        button = gtk.Button(stock=button_text)
        button.set_can_default(True)
        button.show()
        self.add_action_widget(button, response_id)
        return button

    def set_response_sensitive(self, response_id, setting):
        for child in self._action_area.get_children():
            rd = get_response_data(widget, False)
            if rd and rd.response_id == response_id:
                widget.set_sensitive(setting)

    def set_default_response(self, response_id):
        for child in self._action_area.get_children():
            rd = get_response_data(widget, False)
            if rd and rd.response_id == response_id:
                widget.grab_default()

    def response(self, response_id):
        self.emit('response', response_id)

    def set_message_type(self, message_type):
        if self._message_type != message_type:
            self._message_type = message_type

            self.update_colors()
            self.queue_draw()

    def get_message_type(self):
        return self._message_type

    def get_action_area(self):
        return self._action_area

    def get_content_area(self):
        return self._content_area

