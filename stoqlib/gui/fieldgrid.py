# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s):       Johan Dahlin                <jdahlin@async.com.br>
##

# TODO:
#  Focus could be improved, arrows shouldn't focus other widgets
#  Column/List field

"""
Widget containing a Grid of fields
"""

import pickle

import gobject
import pango
import gtk
from gtk import gdk
from gtk import keysyms

from kiwi.python import clamp
from kiwi.utils import gsignal

(FIELD_NONE,
 FIELD_MOVE,
 FIELD_RESIZE) = range(3)

# Bindings
(FIELD_MOVEMENT_HORIZONTAL,
 FIELD_MOVEMENT_VERTICAL,
 FIELD_DELETION) = range(3)


class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __contains__(self, x):
        return self.start < x < self.end


class FieldInfo(object):
    def __init__(self, text, field, x, y):
        self.text = text
        self.widget = field
        self.x = x
        self.y = y
        self.length = -1

    def allocate(self, width, height):
        req_width, req_height = self.widget.size_request()
        self.widget.size_allocate((2 + self.x * width,
                                   2 + self.y * height,
                                   req_width,
                                   req_height))
        self.length = req_width / width

    def find_at(self, x, y):
        wx, wy, ww, wh = self.widget.allocation
        return (x in Range(wx, wx + ww) and
                y in Range(wy, wy + wh))

    def show(self):
        self.widget.show()

    def window_point_resize(self, x, y):
        return False


class FieldGrid(gtk.Layout):
    """
    FieldGrid is a Grid like widget which you can add fields to
    """

    # bindings
    gsignal('move-field', int, int,
            flags=gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION)
    gsignal('remove-field',
            flags=gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION)

    def __init__(self, font, width, height):
        gtk.Layout.__init__(self)
        self.set_flags(self.flags() | gtk.CAN_FOCUS)
        self.drag_dest_set(
            gtk.DEST_DEFAULT_ALL,
            [('OBJECTLIST_ROW', 0, 10),
             ('text/uri-list', 0, 11),
             ('_NETSCAPE_URL', 0, 12)],
            gdk.ACTION_LINK | gdk.ACTION_COPY | gdk.ACTION_MOVE)

        self.font = pango.FontDescription(font)
        self.width = width
        self.height = height
        self._fields = []
        self._moving_field = None
        self._moving_start_x_pointer = 0
        self._moving_start_y_pointer = 0
        self._moving_start_x_position = 0
        self._moving_start_y_position = 0
        self._action_type = FIELD_NONE
        self._selected_field = None


        self._draw_grid = True
        TEXT = '1234567890ABCDEFTI'
        self._layout = self.create_pango_layout(TEXT)
        self._layout.set_font_description(self.font)
        self._field_width = (self._layout.get_pixel_size()[0] / len(TEXT)) + 2
        self._field_height = self._layout.get_pixel_size()[1] + 2

    #
    # Private API
    #

    def _pick_field(self, window_x, window_y):
        for field in self._fields:
            if field.find_at(window_x, window_y):
                return field
        return None

    def _remove_field(self, field):
        self._fields.remove(field)
        self.remove(field.widget)
        if field == self._selected_field:
            self.select_field(None)

    def _add_field(self, text, x, y):
        label = gtk.Label()
        label.set_markup(
            '<span letter_spacing="3072">%s</span>' % (text,))
        label.modify_font(self.font)
        field = FieldInfo(text, label, x, y)
        self._fields.append(field)

        label.connect('size-allocate',
                      self._on_field__size_allocate, field)
        self.put(label, -1, -1)

        return field

    def _set_field_position(self, field, x, y):
        x = clamp(x, 0, self.width - field.length - 1)
        y = clamp(y, 0, self.height - 1)
        if field.x == x and field.y == y:
            return

        field.x, field.y = x, y

        if field.widget.flags() & gtk.VISIBLE:
            self.queue_resize()

    def _get_field_from_widget(self, widget):
        for field in self._fields:
            if field.widget == widget:
                return field
        else:
            raise AssertionError

    def _begin_move_field(self, field, x, y, time):
        if self._moving_field != None:
            raise AssertionError("can't move two fields at once")

        mask = (gdk.BUTTON_RELEASE_MASK | gdk.BUTTON_RELEASE_MASK |
                gdk.POINTER_MOTION_MASK)
        grab = gdk.pointer_grab(self.window, False, mask, None, None,
                                long(time))
        if grab != gdk.GRAB_SUCCESS:
            raise AssertionError("grab failed")

        self._moving_field = field
        self._moving_start_x_pointer = x
        self._moving_start_y_pointer = y
        self._moving_start_x_position = field.x
        self._moving_start_y_position = field.y
        w, h = field.widget.get_size_request()
        self._moving_start_w, self._moving_start_h = w, h

    def _update_move_field(self, x, y):
        field = self._moving_field
        if not field:
            return

        if self._action_type == FIELD_MOVE:
            dx, dy = self._get_coords(
                x - self._moving_start_x_pointer,
                y - self._moving_start_y_pointer)
            self._set_field_position(field,
                                     self._moving_start_x_position + dx,
                                     self._moving_start_y_position + dy)

    def _end_move_field(self, time):
        if not self._moving_field:
            return

        gdk.pointer_ungrab(long(time))
        self._moving_field = None

    def _get_coords(self, x, y):
        """
        Returns the grid coordinates given absolute coordinates
        @param x: absolute x
        @param y: absoluyte y
        @returns: (gridx, gridy)
        """
        return (int(float(x) / (self._field_width + 1)),
                int(float(y) / (self._field_height + 1)))

    def _on_field__size_allocate(self, label, event, field):
        field.allocate(self._field_width + 1, self._field_height + 1)

    #
    # GtkWidget
    #

    def do_realize(self):
        gtk.Layout.do_realize(self)
        input_window = gdk.Window(
            self.get_parent_window(),
            window_type=gdk.WINDOW_CHILD,
            x=self.allocation.x,
            y=self.allocation.y,
            width=self.allocation.width,
            height=self.allocation.height,
            wclass=gdk.INPUT_ONLY,
            visual=self.get_visual(),
            colormap=self.get_colormap(),
            event_mask=(self.get_events() |
                        (gdk.BUTTON_PRESS_MASK |
                         gdk.BUTTON_RELEASE_MASK |
                         gdk.KEY_PRESS_MASK |
                         gdk.KEY_RELEASE_MASK |
                         gdk.ENTER_NOTIFY_MASK |
                         gdk.LEAVE_NOTIFY_MASK)))
        input_window.set_user_data(self)

        self.modify_bg(gtk.STATE_NORMAL, gdk.color_parse('white'))
        gc = gdk.GC(self.window,
                    line_style=gdk.LINE_ON_OFF_DASH,
                    line_width=2)
        gc.set_rgb_fg_color(gdk.color_parse('blue'))
        self._selection_gc = gc

        gc = gdk.GC(self.window)
        gc.set_rgb_fg_color(gdk.color_parse('grey80'))
        self._grid_gc = gc

        gc = gdk.GC(self.window)
        gc.set_rgb_fg_color(gdk.color_parse('black'))
        self._border_gc = gc

    def do_size_request(self, req):
        border_width = 1
        req.width = self.width * (self._field_width + border_width) + border_width
        req.height = self.height * (self._field_height + border_width) + border_width

    def do_expose_event(self, event):
        window = event.window

        if not self.flags() & gtk.REALIZED:
            return

        for c in self._fields:
            self.propagate_expose(c.widget, event)


        fw = self._field_width + 1
        fh = self._field_height + 1

        width = (self.width * fw) - 1
        height = (self.height * fh) - 1
        window.draw_rectangle(self._border_gc, False, 0, 0,
                              width+1, height+1)

        if self._draw_grid:
            grid_gc = self._grid_gc

            for x in range(self.width):
                window.draw_line(grid_gc,
                                 x * fw, 0,
                                 x * fw, height)

            for y in range(self.height):
                 window.draw_line(grid_gc,
                                  0, y * fh,
                                  width, y * fh)

        if self._selected_field:
            gc = self._selection_gc
            c = self._selected_field
            cx, cy, cw, ch = c.widget.allocation
            window.draw_rectangle(gc, False,
                                  cx - 1, cy - 1, cw + 2, ch + 2)

    def do_button_press_event(self, event):
        x, y = int(event.x), int(event.y)

        field = self._pick_field(x, y)
        self.select_field(field)

        self.grab_focus()

        if not field:
            return

        if not self._moving_field:
            if field.window_point_resize(x, y):
                self._action_type = FIELD_RESIZE
            else:
                self._action_type = FIELD_MOVE

            self._begin_move_field(field, x, y, event.time)

        return False

    def do_button_release_event(self, event):
        self._update_move_field(int(event.x), int(event.y))
        self._end_move_field(event.time)

        return False

    def do_motion_notify_event(self, event):
        if self._moving_field != None:
            self._update_move_field(int(event.x), int(event.y))

    def do_key_press_event(self, event):
        if self._moving_field:
            return

        if gtk.Layout.do_key_press_event(self, event):
            return True

        return True

    def do_drag_drop(self, context, x, y, time):
        return True

    def do_drag_data_received(self, context, x, y, data, info, time):
        if data.type == 'OBJECTLIST_ROW':
            row = pickle.loads(data.data)
            x, y = self._get_coords(x, y)
            if self.objectlist_dnd_handler(row, x, y):
                context.finish(True, False, time)
        elif data.type == '_NETSCAPE_URL':
            d = data.data.split('\n')[1]
            d = d.replace('&', '&amp;')
            x, y = self._get_coords(x, y)
            field = self.add_field(d, x, y)
            field.show()
            self.select_field(field)
            context.finish(True, False, time)

        context.finish(False, False, time)

    def do_focus(self, direction):
        self.set_flags(~self.flags() & gtk.CAN_FOCUS)
        res = gtk.Layout.do_focus(self, direction)
        self.set_flags(self.flags() | gtk.CAN_FOCUS)

        return res

    #
    # FieldGrid
    #

    def do_move_field(self, movement_type, delta):
        field = self._selected_field
        if not field:
            return True

        x = field.x
        y = field.y
        if movement_type == FIELD_MOVEMENT_VERTICAL:
            y += delta
        elif movement_type == FIELD_MOVEMENT_HORIZONTAL:
            x += delta
        else:
            raise AssertionError

        self._set_field_position(field, x, y)

    def do_remove_field(self):
        field = self._selected_field
        if field:
            self._remove_field(field)

    #
    # Public API
    #

    def add_field(self, text, x, y):
        """
        Adds a new field to the grid

        @param text: text of the field
        @param x: x position of the field
        @param y: y position of the field
        """
        return self._add_field(text, x, y)

    def select_field(self, field):
        """
        Selects a field
        @param field: the field to select, must be FieldInfo or None
        """
        if field == self._selected_field:
            return
        self._selected_field = field
        self.queue_resize()
        self.grab_focus()

    def get_fields(self):
        """
        @returns: a list of fields in the grid
        """
        return self._fields

    def objectlist_dnd_handler(self, item, x, y):
        """
        A subclass can implement this to support dnd from
        an ObjectList.
        @param item: the row dragged from the objectlist
        @param x: the x position it was dragged to
        @param y: the y position it was dragged to
        """
        return False

gobject.type_register(FieldGrid)
gtk.binding_entry_add_signal(FieldGrid, keysyms.Up, 0, "move_field",
                             int, FIELD_MOVEMENT_VERTICAL, int, -1)
gtk.binding_entry_add_signal(FieldGrid, keysyms.Down, 0, "move_field",
                             int, FIELD_MOVEMENT_VERTICAL, int, 1)
gtk.binding_entry_add_signal(FieldGrid, keysyms.Left, 0, "move_field",
                             int, FIELD_MOVEMENT_HORIZONTAL, int, -1)
gtk.binding_entry_add_signal(FieldGrid, keysyms.Right, 0, "move_field",
                             int, FIELD_MOVEMENT_HORIZONTAL, int, 1)
gtk.binding_entry_add_signal(FieldGrid, keysyms.Delete, 0, "remove_field")
