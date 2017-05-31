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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

# TODO:
#  Focus could be improved, arrows shouldn't focus other widgets
#  Column/List field

"""Widget containing a Grid of fields
"""

import contextlib
import pickle

from gi.repository import Gtk, Gdk, GLib, GObject, Pango

from kiwi.python import clamp
from kiwi.utils import gsignal

(FIELD_NONE,
 FIELD_MOVE,
 FIELD_RESIZE) = range(3)

# Bindings
(FIELD_MOVEMENT_HORIZONTAL,
 FIELD_MOVEMENT_VERTICAL,
 FIELD_DELETION) = range(3)

_cursors = {}

_selection_color = (0.0, 0.0, 1.0)  # blue
_grid_color = (0.8, 0.8, 0.8)  # grey80
_field_border_color = (0.0, 0.0, 0.0)  # black
_border_color = (0.0, 0.0, 0.0)  # black


@contextlib.contextmanager
def _cc_context(cc):
    cc.save()
    yield
    cc.restore()


def _get_cursor(gdk_pos):
    # Do a lazy initialization of those Gdk.Cursor objects
    # If we initialize them too early (e.g. in the module) they would
    # break Stoq running on non graphical environments.
    c = _cursors.get(gdk_pos, None)
    if c is not None:
        return c

    return _cursors.setdefault(gdk_pos, Gdk.Cursor.new(gdk_pos))


class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __contains__(self, x):
        return self.start <= x <= self.end


class FieldInfo(object):
    def __init__(self, grid, name, widget, x, y, width=-1, height=1, model=None):
        if width == -1:
            width = len(name)
        self.grid = grid
        self.name = name
        self.widget = widget
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.model = model

    def update_label(self, text):
        string = '<span letter_spacing="3072">{}</span>'.format(
            GLib.markup_escape_text(text))
        self.widget.set_markup(string)
        self.widget.set_tooltip_markup(string)

    def allocate(self, width, height):
        rect = Gdk.Rectangle()
        rect.x = (self.x * width) - 1
        rect.y = (self.y * height) - 1
        rect.width = (self.width * width) + 2
        rect.height = (self.height * height) + 3
        self.widget.size_allocate(rect)

    def find_at(self, x, y):
        alloc = self.widget.get_allocation()
        wx, wy, ww, wh = alloc.x, alloc.y, alloc.width, alloc.height
        return (x in Range(wx, wx + ww) and
                y in Range(wy, wy + wh))

    def show(self):
        self.widget.show()

    def get_cursor(self, x, y):
        a = self.widget.get_allocation()
        cx = a.x + 1
        cy = a.y + 1
        cw = a.width
        ch = a.height
        intop = y in Range(cy - 1, cy + 1)
        inbottom = y in Range(cy + ch - 3, cy + ch)

        if x in Range(cx - 1, cx + 1):
            if intop:
                return  # _get_cursor(Gdk.CursorType.TOP_LEFT_CORNER)
            elif inbottom:
                return  # _get_cursor(Gdk.CursorType.BOTTOM_LEFT_CORNER)
            else:
                return  # _get_cursor(Gdk.CursorType.LEFT_SIDE)
        elif x in Range(cx + cw - 2, cx + cw + 1):
            if intop:
                return  # _get_cursor(Gdk.CursorType.TOP_RIGHT_CORNER)
            elif inbottom:
                return _get_cursor(Gdk.CursorType.BOTTOM_RIGHT_CORNER)
            else:
                return _get_cursor(Gdk.CursorType.RIGHT_SIDE)
        elif intop:
            return  # _get_cursor(Gdk.CursorType.TOP_SIDE)
        elif inbottom:
            return _get_cursor(Gdk.CursorType.BOTTOM_SIDE)


class FieldGrid(Gtk.Layout):
    """FieldGrid is a Grid like widget which you can add fields to

    * **field-added** (object): Emitted when a field is added to the grid
    * **field-removed** (object): Emitted when a field is removed
      from the grid
    * ** selection-changed** (object): Emitted when a field is selected or
      deselected by the user.
    """

    gsignal('selection-changed', object,
            flags=GObject.SignalFlags.RUN_LAST | GObject.SignalFlags.ACTION)
    gsignal('field-added', object)
    gsignal('field-removed', object)

    def __init__(self, font, width, height):
        super(FieldGrid, self).__init__()

        self.set_can_focus(True)
        self.drag_dest_set(
            Gtk.DestDefaults.ALL,
            [Gtk.TargetEntry.new('OBJECTLIST_ROW', 0, 10),
             Gtk.TargetEntry.new('text/uri-list', 0, 11),
             Gtk.TargetEntry.new('_NETSCAPE_URL', 0, 12)],
            Gdk.DragAction.LINK | Gdk.DragAction.COPY | Gdk.DragAction.MOVE)

        self.font = Pango.FontDescription(font)
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

    def _remove_selected_field(self):
        field = self._selected_field
        if field:
            self._remove_field(field)

    def _remove_field(self, field):
        if field == self._selected_field:
            self.select_field(None)

        self._fields.remove(field)
        self.remove(field.widget)
        self.emit('field-removed', field)

    def _add_field(self, name, description, x, y, width=-1, height=1, model=None):
        label = Gtk.Label()
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_alignment(0, 0)
        label.set_padding(2, 4)
        if not description:
            description = name
        label.modify_font(self.font)
        field = FieldInfo(self, name, label, x, y, width, height, model)
        field.update_label(description)
        self._fields.append(field)
        self.emit('field-added', field)

        label.connect('size-allocate',
                      self._on_field__size_allocate, field)
        self.put(label, -1, -1)
        return field

    def _set_field_position(self, field, x, y):
        x = clamp(x, 0, self.width - field.width - 1)
        y = clamp(y, 0, self.height - field.height - 1)
        if field.x == x and field.y == y:
            return

        field.x, field.y = x, y

        if field.widget.props.visible:
            self.queue_resize()
        self.emit('selection-changed', field)

    def _resize_field(self, field, width, height):
        width = clamp(width, 1, self.width - field.x - 1)
        height = clamp(height, 1, self.height - field.y - 1)
        if field.width == width and field.height == height:
            return

        field.width, field.height = width, height

        if field.widget.props.visible:
            self.queue_resize()
        self.emit('selection-changed', field)

    def _get_field_from_widget(self, widget):
        for field in self._fields:
            if field.widget == widget:
                return field
        else:
            raise AssertionError

    def _begin_move_field(self, field, x, y, time):
        if self._moving_field is not None:
            raise AssertionError("can't move two fields at once")

        mask = (Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK |
                Gdk.EventMask.POINTER_MOTION_MASK)
        grab = Gdk.pointer_grab(self.get_window(), False, mask, None, None, time)
        if grab != Gdk.GrabStatus.SUCCESS:
            raise AssertionError("grab failed")

        self._moving_field = field
        self._moving_start_x_pointer = x
        self._moving_start_y_pointer = y
        self._moving_start_x_position = field.x
        self._moving_start_y_position = field.y
        self._moving_start_width = field.width
        self._moving_start_height = field.height
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
        elif self._action_type == FIELD_RESIZE:
            dx, dy = self._get_coords(
                x - self._moving_start_x_pointer,
                y - self._moving_start_y_pointer)
            self._resize_field(field,
                               self._moving_start_width + dx,
                               self._moving_start_height + dy)

    def _end_move_field(self, time):
        if not self._moving_field:
            return

        Gdk.pointer_ungrab(time)
        self._moving_field = None

    def _get_coords(self, x, y):
        """Returns the grid coordinates given absolute coordinates
        :param x: absolute x
        :param y: absoluyte y
        :returns: (gridx, gridy)
        """
        return (int(float(x) / (self._field_width + 1)),
                int(float(y) / (self._field_height + 1)))

    def _move_field(self, movement_type, delta):
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

    def _on_field__size_allocate(self, label, event, field):
        field.allocate(self._field_width + 1, self._field_height + 1)

    #
    # GtkWidget
    #

    def do_realize(self):
        Gtk.Layout.do_realize(self)
        # Use the same Gdk.window (from Gtk.Layout) to capture these events.
        window = self.get_window()
        events = (
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.KEY_PRESS_MASK |
            Gdk.EventMask.KEY_RELEASE_MASK |
            Gdk.EventMask.ENTER_NOTIFY_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        original_events = self.get_events()
        if isinstance(original_events, Gdk.EventMask):
            events |= original_events

        window.set_events(events)

        self.override_background_color(
            Gtk.StateType.NORMAL, Gdk.RGBA(1.0, 1.0, 1.0, 1.0))

        width = self.width * (self._field_width + 1) + 1
        height = self.height * (self._field_height + 1) + 1
        self.set_size(width, height)

    def do_size_request(self, req):
        border_width = 1
        req.width = self.width * (self._field_width + border_width) + border_width
        req.height = self.height * (self._field_height + border_width) + border_width

    def do_draw(self, cc):
        Gtk.Layout.do_draw(self, cc)

        hvalue = self.get_hadjustment().get_value()
        vvalue = self.get_vadjustment().get_value()
        # Since we are drawing in the widget and not in the bin window
        # we need to translate the coordinates or else our drawing would
        # be static when scrolling
        cc.translate(-hvalue, -vvalue)

        fw = self._field_width + 1
        fh = self._field_height + 1

        width = (self.width * fw) - 1
        height = (self.height * fh) - 1

        with _cc_context(cc):
            cc.set_source_rgb(*_border_color)
            cc.rectangle(0, 0, width + 1, height + 1)
            cc.stroke()

        if self._draw_grid:
            with _cc_context(cc):
                cc.set_line_width(0.25)
                cc.set_source_rgb(*_grid_color)

                for x in range(self.width):
                    cc.move_to(x * fw, 0)
                    cc.line_to(x * fw, height)

                for y in range(self.height):
                    cc.move_to(0, y * fh)
                    cc.line_to(width, y * fh)

                cc.stroke()

        fields = self._fields[:]
        if self._selected_field:
            with _cc_context(cc):
                cc.set_line_width(2)
                cc.set_dash([4.0, 4.0, 4.0])
                cc.set_source_rgb(*_selection_color)
                field = self._selected_field
                rect = field.widget.get_allocation()
                cc.rectangle(rect.x + 1, rect.y + 1,
                             rect.width - 2, rect.height - 2)
                cc.stroke()

                fields.remove(field)

        with _cc_context(cc):
            cc.set_line_width(0.25)
            cc.set_source_rgb(*_field_border_color)
            for field in fields:
                rect = field.widget.get_allocation()
                cc.rectangle(rect.x + 1, rect.y + 1, rect.width - 2, rect.height - 3)
                cc.stroke()

    def do_button_press_event(self, event):
        x, y = int(event.x), int(event.y)

        field = self._pick_field(x, y)
        self.select_field(field)

        self.grab_focus()

        if not field:
            return

        if not self._moving_field:
            if field.get_cursor(x, y):
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
        if self._moving_field is not None:
            self._update_move_field(int(event.x), int(event.y))
        else:
            field = self._pick_field(event.x, event.y)
            cursor = None
            if field:
                cursor = field.get_cursor(event.x, event.y)
            self.get_window().set_cursor(cursor)

    def do_key_press_event(self, event):
        if self._moving_field:
            return

        if event.keyval == Gdk.KEY_Up:
            self._move_field(FIELD_MOVEMENT_VERTICAL, -1)
        elif event.keyval == Gdk.KEY_Down:
            self._move_field(FIELD_MOVEMENT_VERTICAL, 1)
        elif event.keyval == Gdk.KEY_Left:
            self._move_field(FIELD_MOVEMENT_HORIZONTAL, -1)
        elif event.keyval == Gdk.KEY_Right:
            self._move_field(FIELD_MOVEMENT_HORIZONTAL, 1)
        elif event.keyval == Gdk.KEY_Delete:
            self._remove_selected_field()

        if Gtk.Layout.do_key_press_event(self, event):
            return True

        return True

    def do_drag_drop(self, context, x, y, time):
        return True

    # pylint: disable=E1120
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
    # pylint: enable=E1120

    def do_focus(self, direction):
        self.set_can_focus(False)
        res = Gtk.Layout.do_focus(self, direction)
        self.set_can_focus(True)

        return res

    #
    # Public API
    #

    def add_field(self, text, description, x, y, width=-1, height=1, model=None):
        """Adds a new field to the grid

        :param text: text of the field
        :param description: description of the field
        :param x: x position of the field
        :param y: y position of the field
        """
        return self._add_field(text, description, x, y, width, height, model)

    def select_field(self, field):
        """Selects a field
        :param field: the field to select, must be FieldInfo or None
        """
        if field == self._selected_field:
            return
        self._selected_field = field
        self.queue_resize()
        self.grab_focus()
        self.emit('selection-changed', field)

    def get_selected_field(self):
        """ Returns the currently selected field
        :returns: the currently selected field
        :rtype: FieldInfo
        """
        return self._selected_field

    def get_fields(self):
        """ Returns a list of fields in the grid
        :returns: a list of fields in the grid
        """
        return self._fields

    def objectlist_dnd_handler(self, item, x, y):
        """A subclass can implement this to support dnd from
        an ObjectList.
        :param item: the row dragged from the objectlist
        :param x: the x position it was dragged to
        :param y: the y position it was dragged to
        """
        return False

    def resize(self, width, height):
        """
        Resize the grid.
        :param width: the new width
        :param height: the new height
        """
        self.width = width
        self.height = height
        self.queue_resize()

GObject.type_register(FieldGrid)
