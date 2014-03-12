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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

# Implementatiopn of the kanban process view
# http://en.wikipedia.org/wiki/Kanban

import pickle

import gobject
import gtk
from kiwi.python import Settable
from kiwi.utils import gsignal
from kiwi.ui.objectlist import Column, ObjectList


class KanbanObjectListColumn(Column):
    def create_renderer(self, model):
        renderer = CellRendererTextBox()
        renderer.props.xpad = 12
        renderer.props.ypad = 12
        return renderer, 'markup'


class CellRendererTextBox(gtk.CellRendererText):

    PADDING = 3
    SIZE = 6

    #: the magin color of the renderer, this the part to the left of it,
    #: indicating a category color
    margin_color = gobject.property(type=str)

    def do_render(self, drawable, widget, background_area, cell_area,
                  expose_area, flags):
        if flags & gtk.CELL_RENDERER_SELECTED:
            state = gtk.STATE_SELECTED
        else:
            state = gtk.STATE_NORMAL

        if type(drawable) == gtk.gdk.Pixmap:
            cr = drawable.cairo_create()
            cr.set_source_color(widget.style.bg[gtk.STATE_SELECTED])
            cr.paint()
        else:
            widget.style.paint_box(drawable, state, gtk.SHADOW_IN,
                                   None, widget, "frame",
                                   cell_area.x + self.PADDING,
                                   cell_area.y + self.PADDING,
                                   cell_area.width - (self.PADDING * 2),
                                   cell_area.height - (self.PADDING * 2))
        color = self.props.margin_color
        if color is not None:
            cr = drawable.cairo_create()
            cr.rectangle(cell_area.x + self.PADDING - 1,
                         cell_area.y + self.PADDING,
                         4, cell_area.height - (self.PADDING * 2))
            cr.set_source_color(gtk.gdk.color_parse(color))
            cr.fill()

        gtk.CellRendererText.do_render(self, drawable, widget, background_area,
                                       cell_area, expose_area, flags)

    def on_get_size(self, widget, cell_area=None):
        if cell_area is None:
            return (0, 0, 0, 0)
        else:
            return (cell_area.x - self.SIZE,
                    cell_area.y - self.SIZE,
                    cell_area.width + (self.SIZE * 2),
                    cell_area.height + (self.SIZE * 2))

gobject.type_register(CellRendererTextBox)


class KanbanViewColumn(object):
    """A column in a KanbanView

    It just has a title and can be cleared via :attr:`.clear` and
    you can append an item via :attr:`.append_item`
    """
    def __init__(self, title):
        self.title = title
        self.view = None
        self.object_list = None

    def clear(self):
        """Clear this view, eg remove all the items"""
        self.object_list.clear()

    def append_item(self, item):
        """Append an item to the view"""
        self.object_list.append(item)


class KanbanView(gtk.Frame):
    """
    This is a kanban view which can be used to display a set
    of columns with boxes that can be rearranged.

    """
    __gtype_name__ = 'KanbanView'

    TREEVIEW_DND_TARGETS = [
        ('text/plain', 0, 1),
    ]

    # item activated
    gsignal('item-activated', object)
    gsignal('item-dragged', object, object, retval=bool)
    gsignal('item-popup-menu', object, object)
    gsignal('selection-changed', object)
    gsignal('activate-link', object)

    def __init__(self):
        super(KanbanView, self).__init__()
        self.hbox = gtk.HBox()
        self.add(self.hbox)
        self.hbox.show()

        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # column title -> column
        self._columns = {}
        # column title -> objectlist
        self._treeviews = {}
        self._selected_iter = None
        self._selected_treeview = None
        self._message_label = None

    #
    # Public API
    #

    def clear(self):
        """
        Clears the view and all it's columns.
        """
        self.clear_message()
        for column in self._columns.values():
            column.clear()

    def get_column_by_title(self, column_title):
        """
        Get a column given a title

        :returns: a column or ``None`` if none are found
        """
        return self._columns.get(column_title)

    def add_column(self, column):
        """
        Adds a new column to the view

        :param KanbanViewColumn column: column to add
        """
        object_list = self._create_list(column.title)
        self.hbox.pack_start(object_list)
        object_list.show()

        self._columns[column.title] = column
        self._treeviews[column.title] = object_list.get_treeview()

        column.view = self
        column.object_list = object_list

    def enable_editing(self):
        """
        Makes it possible to edit items within this treeview.

        You also need to return ``True`` in the ::item-dragged callback
        for an item to be draggable.
        """
        for treeview in self._treeviews.values():
            treeview.enable_model_drag_source(
                gtk.gdk.BUTTON1_MASK, self.TREEVIEW_DND_TARGETS,
                gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
            treeview.enable_model_drag_dest(
                self.TREEVIEW_DND_TARGETS, gtk.gdk.ACTION_DEFAULT)
            treeview.connect(
                "drag-data-get", self._on_drag_data_get_data)
            treeview.connect(
                "drag-data-received", self._on_drag_data_received_data)

    def select(self, item):
        """
        Select an item in the view

        :param item: the item to select or ``None`` to unselect all
        """
        # FIXME: How to make this cheaper with larger lists?
        for treeview in self._treeviews.values():
            for row in treeview.get_model():
                if row[0] == item:
                    self._maybe_selection_changed(treeview, row.iter)
                    return

        self._maybe_selection_changed(None, None)

    def get_selected_item(self):
        """
        Get the currently selected item from the view

        :returns: the selected item or ``None`` if no items are selected
        """
        if self._message_label:
            return None
        if self._selected_iter is not None:
            model = self._selected_treeview.get_model()
            return model[self._selected_iter][0]

    def render_item(self, column, renderer, item):
        """
        Renders an item, this is an optional hook that can be implemented by
        a subclass.

        :param column: the treeview column
        :param renderer: the cell renderer
        :parma item: the item
        """

    def get_n_items(self):
        return sum(len(column.object_list.get_model())
                   for column in self._columns.values())

    def set_message(self, markup):
        """Adds a message on top of the treeview rows
        :param markup: PangoMarkup with the text to add
        """
        if self._message_label is None:
            self._viewport = gtk.Viewport()
            self._viewport.set_shadow_type(gtk.SHADOW_NONE)
            self.remove(self.hbox)
            self.add(self._viewport)

            self._message_box = gtk.EventBox()
            self._message_box.modify_bg(
                gtk.STATE_NORMAL, gtk.gdk.color_parse('white'))
            self._viewport.add(self._message_box)
            self._message_box.show()

            self._message_label = gtk.Label()
            self._message_label.connect(
                'activate-link', self._on_message_label__activate_link)
            self._message_label.set_use_markup(True)
            self._message_label.set_alignment(0, 0)
            self._message_label.set_padding(12, 12)
            self._message_box.add(self._message_label)
            self._message_label.show()

        self._message_label.set_label(markup)
        self._viewport.show()

    def clear_message(self):
        if self._message_label is None:
            return

        children = self.get_children()
        if self._viewport in children:
            self.remove(self._viewport)
        if self.hbox not in children:
            self.add(self.hbox)

        self._message_label.set_label("")

    #
    # Private
    #

    def _create_list(self, column_title):
        object_list = ObjectList([
            KanbanObjectListColumn('markup', title=column_title,
                                   data_type=str, use_markup=True,
                                   expand=True),
        ])
        object_list.connect('row-activated',
                            self._on_row_activated)
        object_list.connect('right-click',
                            self._on_right_click)
        sw = object_list.get_scrolled_window()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_NONE)

        treeview = object_list.get_treeview()
        treeview.set_name(column_title)
        treeview.connect(
            "button-press-event", self._on_button_press_event)
        treeview.set_rules_hint(False)

        column = object_list.get_column_by_name('markup')
        column.treeview_column.set_clickable(False)

        white = gtk.gdk.color_parse('white')
        treeview.modify_base(gtk.STATE_ACTIVE, white)
        treeview.modify_base(gtk.STATE_SELECTED, white)

        object_list.set_cell_data_func(self._on_results__cell_data_func)
        return object_list

    def _on_results__cell_data_func(self, column, renderer, item, text):
        self.render_item(column, renderer, item)
        return text

    def _maybe_selection_changed(self, treeview=None, titer=None):
        if titer == self._selected_iter:
            return

        for check_treeview in self._treeviews.values():
            selection = check_treeview.get_selection()
            if check_treeview == treeview and titer is not None:
                selection.select_iter(titer)
            else:
                selection.unselect_all()

        self._selected_iter = titer
        self._selected_treeview = treeview

        if titer is not None:
            item = treeview.get_model()[titer][0]
        else:
            item = None
        self.emit('selection-changed', item)

    #
    # Callbacks
    #

    def _on_message_label__activate_link(self, label, uri):
        self.emit('activate-link', uri)
        return True

    def _on_row_activated(self, olist, item):
        self.emit('item-activated', item)

    def _on_right_click(self, olist, item, event):
        self.emit('item-popup-menu', item, event)

    def _on_button_press_event(self, treeview, event):
        retval = treeview.get_path_at_pos(int(event.x),
                                          int(event.y))
        model = treeview.get_model()
        if retval:
            titer = model[retval[0]].iter
        else:
            titer = None

        self._maybe_selection_changed(treeview, titer)

    def _on_drag_data_get_data(self, treeview, context,
                               selection, target_id, etime):
        treeselection = treeview.get_selection()
        model, titer = treeselection.get_selected()
        if titer is None:
            return

        selection_data = self._create_selection_data(treeview, titer)
        selection.set(selection.target, 8, selection_data)

    def _create_selection_data(self, treeview, titer):
        model = treeview.get_model()
        path = model[titer].path
        return pickle.dumps([treeview.get_name(), path])

    def _load_selection_data(self, selection_data):
        column_title, path = pickle.loads(selection_data)
        treeview = self._treeviews[column_title]
        model = treeview.get_model()
        return model[path][0]

    def _on_drag_data_received_data(self, treeview, context, x, y,
                                    selection, info, etime):
        model = treeview.get_model()
        if selection.data is None:
            context.finish(False, False, etime)
            return
        item = self._load_selection_data(selection.data)
        column = self._columns[treeview.get_name()]
        retval = self.emit('item-dragged', column, item)
        if retval is False:
            context.finish(False, False, etime)
            return

        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            path, position = drop_info
            titer = model.get_iter(path)
            if (position == gtk.TREE_VIEW_DROP_BEFORE or
                position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
                titer = model.insert_before(titer, [item])
            else:
                titer = model.insert_after(titer, [item])
        else:
            titer = model.append([item])

        if context.action == gtk.gdk.ACTION_MOVE:
            context.finish(True, True, etime)

        treeview.grab_focus()
        self._maybe_selection_changed(treeview, titer)

gobject.type_register(KanbanView)


def main():
    win = gtk.Window()
    win.set_size_request(600, 300)
    win.connect('destroy', gtk.main_quit)

    kanban = KanbanView()
    for title in ['Opened', 'Approved', 'Executing', 'Finished']:
        kanban.add_column(KanbanViewColumn(title))

    kanban.connect('item-dragged', lambda *x: True)
    kanban.enable_editing()
    items = [Settable(name='Ronaldo', phone='1972-2878'),
             Settable(name='Gabriel', phone='1234-5678'),
             Settable(name='João Paulo', phone='2982-8278'),
             Settable(name='Bellini', phone='2982-2909'),
             Settable(name='Johan', phone='2929-0202')]
    column = kanban.get_column_by_title('Opened')
    for item in items:
        column.append_item(item)
    win.add(kanban)

    win.show_all()

    gtk.main()

if __name__ == '__main__':
    main()
