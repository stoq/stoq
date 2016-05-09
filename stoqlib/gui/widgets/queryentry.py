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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import gtk
import glib
from kiwi.ui.cellrenderer import ComboDetailsCellRenderer
from kiwi.ui.entry import ENTRY_MODE_DATA
from kiwi.ui.popup import PopupWindow
from kiwi.utils import gsignal

from stoqlib.api import api
from stoqlib.database.queryexecuter import QueryExecuter
from stoqlib.domain.person import Client, ClientView, Supplier, SupplierView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.personeditor import ClientEditor, SupplierEditor
from stoqlib.gui.search.personsearch import ClientSearch, SupplierSearch
from stoqlib.gui.search.searchfilters import StringSearchFilter
from stoqlib.gui.templates.persontemplate import BasePersonRoleEditor
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.formatters import format_address
from stoqlib.lib.translation import stoqlib_gettext as _


_NEW_ITEM_MARKER = object()
_LOADING_ITEM_MARKER = object()
(COL_ITEM,
 COL_MARKUP,
 COL_TOOLTIP,
 COL_SPINNER_ACTIVE,
 COL_SPINNER_PULSE) = range(5)


class _QueryEntryPopup(PopupWindow):

    gsignal('item-selected', object, bool)
    gsignal('create-item')

    PROPAGATE_KEY_PRESS = True
    GRAB_WINDOW = False

    def __init__(self, entry_gadget):
        self.loading = False
        self.entry_gadget = entry_gadget
        super(_QueryEntryPopup, self).__init__(entry_gadget.entry)

    #
    #  Public API
    #

    def set_loading(self, loading):
        if loading == self.loading:
            return

        self.loading = loading
        self._model.clear()

        if loading:
            self._treeview.insert_column(self._spinner_column, 0)
            self._model.append(
                (_LOADING_ITEM_MARKER, self.entry_gadget.LOADING_ITEMS_TEXT,
                 None, True, 0))
            glib.timeout_add(100, self._pulse_spinner_col)
        else:
            self._treeview.remove_column(self._spinner_column)

    def add_items(self, items):
        self.set_loading(False)
        self._model.clear()

        for item in items:
            label, tooltip = self.entry_gadget.describe_item(item)
            self._model.append((item, label, tooltip, False, 0))

        if len(self._model):
            self._selection.select_path(self._model[0].path)

        self._model.append(
            (_NEW_ITEM_MARKER, self.entry_gadget.NEW_ITEM_TEXT, None, False, 0))
        glib.idle_add(self._resize)

    def scroll(self, relative=None, absolute=None):
        model, titer = self._selection.get_selected()

        if titer is None:
            row_no = 0
        elif relative is not None:
            row_no = model[titer].path[0] + relative
        elif absolute is not None:
            row_no = absolute
        else:
            raise TypeError("needs relative or absolute")

        if row_no < 0:
            path = (0, )
        elif row_no >= len(model):
            path = (len(model) - 1, )
        else:
            path = (row_no, )

        titer = model[path].iter
        self._selection.select_iter(titer)
        self._treeview.scroll_to_cell(path, None, False, 0, 0)

    #
    #  EntryPopup
    #

    def confirm(self, fallback_to_search=False):
        self._activate_selected_item(fallback_to_search=fallback_to_search)

    def handle_key_press_event(self, event):
        keyval = event.keyval
        # By default the PopupWindow will call confirm for both Return and
        # KP_Enter, but also for Tab and Space. We want to fallback to search
        # in those specific cases
        if keyval in [gtk.keysyms.Return, gtk.keysyms.KP_Enter]:
            self.confirm(fallback_to_search=True)
            return True

        return super(_QueryEntryPopup, self).handle_key_press_event(event)

    def get_main_widget(self):
        vbox = gtk.VBox()

        self._sw = gtk.ScrolledWindow()
        self._sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        vbox.pack_start(self._sw)

        self._model = gtk.ListStore(object, str, str, bool, int)
        self._treeview = gtk.TreeView(self._model)
        self._treeview.connect('motion-notify-event',
                               self._on_treeview__motion_notify_event)
        self._treeview.connect('button-release-event',
                               self._on_treeview__button_release_event)
        self._treeview.add_events(
            gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.KEY_PRESS_MASK)

        self._treeview.modify_base(gtk.STATE_ACTIVE,
                                   self._get_selection_color())
        self._treeview.set_tooltip_column(COL_TOOLTIP)
        self._treeview.set_enable_search(False)

        self._selection = self._treeview.get_selection()
        self._selection.set_mode(gtk.SELECTION_BROWSE)

        self._spinner_renderer = gtk.CellRendererSpinner()
        self._spinner_column = gtk.TreeViewColumn(
            '', self._spinner_renderer,
            active=COL_SPINNER_ACTIVE, pulse=COL_SPINNER_PULSE)

        self._renderer = ComboDetailsCellRenderer(use_markup=True)
        self._treeview.append_column(
            gtk.TreeViewColumn('', self._renderer, label=COL_MARKUP))

        self._treeview.set_headers_visible(False)
        self._sw.add(self._treeview)

        vbox.show_all()
        return vbox

    def get_size(self, allocation, monitor):
        self._treeview.realize()
        width = allocation.width

        rows = len(self._treeview.get_model())
        cell_area = self._treeview.get_background_area(
            0, self._treeview.get_column(0))
        cell_height = cell_area.height
        # Use half of the available screen space
        height = min(max(cell_height * rows, cell_height), monitor.height / 2)
        height += self.FRAME_PADDING[0] + self.FRAME_PADDING[1]

        return width, height

    def popup(self):
        self.set_loading(True)
        super(_QueryEntryPopup, self).popup()
        self._treeview.set_size_request(-1, -1)
        self.widget.grab_focus()
        self.widget.select_region(len(self.widget.get_text()), -1)

    def popdown(self):
        super(_QueryEntryPopup, self).popdown()
        self.set_loading(False)

    #
    #  Private
    #

    def _resize(self):
        widget = self.get_widget_for_popup()
        allocation = widget.get_allocation()
        screen = widget.get_screen()
        window = widget.get_window()
        # FIXME: window will be None on a test, but it is hard to tell which
        # one since it breaks one randomly because of the idle_add.
        if window is not None:
            monitor_num = screen.get_monitor_at_window(widget.get_window())
        else:
            monitor_num = 0
        monitor = screen.get_monitor_geometry(monitor_num)

        self.set_size_request(*self.get_size(allocation, monitor))
        self._treeview.set_size_request(-1, -1)

    def _pulse_spinner_col(self):
        for item in self._model:
            if not item[COL_SPINNER_ACTIVE]:
                continue
            item[COL_SPINNER_PULSE] += 1
        return self.loading

    def _select_item(self, item, fallback_to_search=False):
        if item is _LOADING_ITEM_MARKER:
            pass
        elif item is _NEW_ITEM_MARKER:
            self.popdown()
            self.emit('create-item')
        else:
            self.emit('item-selected', item, fallback_to_search)

    def _get_selection_color(self):
        settings = gtk.settings_get_default()
        for line in settings.props.gtk_color_scheme.split('\n'):
            if not line:
                continue
            key, value = line.split(' ')
            if key == 'selected_bg_color:':
                return gtk.gdk.color_parse(value)
        return self.widget.style.base[gtk.STATE_SELECTED]

    def _select_path_for_event(self, event):
        path = self._treeview.get_path_at_pos(int(event.x), int(event.y))
        if not path:
            return

        path, column, x, y = path
        self._selection.select_path(path)
        self._treeview.set_cursor(path)

    def _activate_selected_item(self, fallback_to_search=False):
        model, treeiter = self._selection.get_selected()
        self._select_item(treeiter and model[treeiter][COL_ITEM],
                          fallback_to_search=fallback_to_search)

    #
    #  Callbacks
    #

    def _on_treeview__motion_notify_event(self, treeview, event):
        self._select_path_for_event(event)

    def _on_treeview__button_release_event(self, treeview, event):
        self._select_path_for_event(event)
        self._activate_selected_item()


class QueryEntryGadget(object):
    """This gadget modifies a ProxyEntry to behave like a ProxyComboEntry.

    When instanciated, the gadget will remove the entry from the editor, add
    a gtk.HBox on its place, and re-attach the entry to the newly created
    hbox. This hbox will also have a button to add/edit a new object.

    There are a few advantages in using this instead of a combo:

    - There is no need to prefill the combo with all the options, which can
      be very slow depending on the number of objects.

    - This allows the user to use a better search mechanism, allowing him to
      filter using multiple keywords and even candidade keys (like a client
      document)
    """

    MIN_KEY_LENGTH = 1
    LOADING_ITEMS_TEXT = _("Loading items...")
    NEW_ITEM_TEXT = _("Create a new item with that name")
    NEW_ITEM_TOOLTIP = _("Create a new item")
    EDIT_ITEM_TOOLTIP = _("Edit the selected item")
    ITEM_EDITOR = None
    SEARCH_CLASS = None
    SEARCH_SPEC = None
    SEARCH_COLUMNS = None

    def __init__(self, entry, store, initial_value=None,
                 parent=None, run_editor=None, edit_button=None):
        """
        :param entry: The entry that we should modify
        :param store: The store that will be used for database queries
        :param initial_value: Initial value for the entry
        :param parent: The parent that should be respected when running other
          dialogs
        """
        super(QueryEntryGadget, self).__init__()

        self._parent = parent
        self._on_run_editor = run_editor
        self._can_edit = False
        self.entry = entry
        self.entry.set_mode(ENTRY_MODE_DATA)
        self.edit_button = edit_button
        self.store = store

        # The filter that will be used. This is not really in the interface.
        # We will just use it to perform the search.
        self._filter = StringSearchFilter('')
        self._executer = QueryExecuter(self.store)
        self._executer.set_search_spec(self.SEARCH_SPEC)
        self._executer.set_filter_columns(self._filter, self.SEARCH_COLUMNS)

        self._last_operation = None
        self._source_id = None
        self._is_person = issubclass(self.ITEM_EDITOR, BasePersonRoleEditor)

        self._setup()
        self.set_value(initial_value, force=True)

    #
    #  Public API
    #

    def set_value(self, obj, force=False):
        if not force and obj == self._current_obj:
            return

        obj = self.store.fetch(obj)
        if obj is not None:
            value = obj.get_description()
            self.entry.prefill([(value, obj)])
            self.update_edit_button(gtk.STOCK_INFO, self.EDIT_ITEM_TOOLTIP)
        else:
            value = ''
            self.entry.prefill([])
            self.update_edit_button(gtk.STOCK_NEW, self.NEW_ITEM_TOOLTIP)

        self._current_obj = obj
        self.entry.update(obj)
        self.entry.set_text(value)

        self._update_widgets()

    def set_editable(self, can_edit):
        self.entry.set_property('editable', can_edit)
        self._update_widgets()

    def update_edit_button(self, stock, tooltip=None):
        image = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU)
        self.edit_button.set_image(image)
        if tooltip is not None:
            self.edit_button.set_tooltip_text(tooltip)

    def get_object_from_item(self, item):
        return item

    def describe_item(self, item):
        raise NotImplementedError

    #
    #  Private
    #

    def _setup(self):
        if self.edit_button is None:
            self._replace_widget()
            self.edit_button = self._add_button(gtk.STOCK_NEW)
        self.edit_button.connect('clicked', self._on_edit_button__clicked)

        self.entry.connect('activate', self._on_entry__activate)
        self.entry.connect('changed', self._on_entry__changed)
        self.entry.connect('notify::sensitive', self._on_entry_sensitive)
        self.entry.connect('key-press-event', self._on_entry__key_press_event)

        self._popup = _QueryEntryPopup(self)
        self._popup.connect('item-selected', self._on_popup__item_selected)
        self._popup.connect('create-item', self._on_popup__create_item)

    def _update_widgets(self):
        self._can_edit = self.entry.get_editable() and self.entry.get_sensitive()
        self.edit_button.set_sensitive(bool(self._can_edit or self._current_obj))

    def _add_button(self, stock):
        image = gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU)
        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        button.set_image(image)
        button.show()
        self.box.pack_start(button, False, False)
        return button

    def _replace_widget(self):
        # This will remove the entry, add a hbox in the entry old position, and
        # reattach the entry to this box. The box will then be used to add two
        # new buttons (one for searching, other for editing/adding new objects
        container = self.entry.parent

        # stolen from gazpacho code (widgets/base/base.py):
        props = {}
        for pspec in gtk.container_class_list_child_properties(container):
            props[pspec.name] = container.child_get_property(self.entry, pspec.name)

        self.box = gtk.HBox()
        self.box.show()
        self.entry.reparent(self.box)
        container.add(self.box)

        for name, value in props.items():
            container.child_set_property(self.box, name, value)

    def _find_items(self, text):
        self._filter.set_state(text)
        state = self._filter.get_state()
        return self._executer.search_async([state], limit=10)

    def _dispatch(self, value):
        self._source_id = None
        if self._last_operation is not None:
            self._last_operation.cancel()
        self._last_operation = self._find_items(value)
        self._last_operation.connect(
            'finish', lambda o: self._popup.add_items(o.get_result()))

    def _run_search(self):
        text = self.entry.get_text()
        if not text:
            return

        item = run_dialog(self.SEARCH_CLASS, self._parent, self.store,
                          double_click_confirm=True, initial_string=text)
        if item:
            self.set_value(self.get_object_from_item(item))

    def _run_editor(self, model=None, description=None):
        with api.new_store() as store:
            model = store.fetch(model)
            if self._on_run_editor is not None:
                retval = self._on_run_editor(store, model,
                                             description=description,
                                             visual_mode=not self._can_edit)
            else:
                rd = run_person_role_dialog if self._is_person else run_dialog
                retval = rd(self.ITEM_EDITOR, self._parent, store, model,
                            description=description,
                            visual_mode=not self._can_edit)

        if store.committed:
            return self.store.fetch(retval)

    #
    #  Callbacks
    #

    def _on_entry__key_press_event(self, window, event):
        keyval = event.keyval
        if keyval == gtk.keysyms.Up or keyval == gtk.keysyms.KP_Up:
            self._popup.scroll(relative=-1)
            return True
        elif keyval == gtk.keysyms.Down or keyval == gtk.keysyms.KP_Down:
            self._popup.scroll(relative=+1)
            return True
        elif keyval == gtk.keysyms.Page_Up:
            self._popup.scroll(relative=-14)
            return True
        elif keyval == gtk.keysyms.Page_Down:
            self._popup.scroll(relative=+14)
            return True
        elif keyval == gtk.keysyms.Escape:
            self._popup.popdown()
            return True

        return False

    def _on_entry__changed(self, entry):
        value = unicode(entry.get_text())
        self.set_value(None)
        if len(value) >= self.MIN_KEY_LENGTH:
            if self._source_id is not None:
                glib.source_remove(self._source_id)
            self._source_id = glib.timeout_add(150, self._dispatch, value)
            if not self._popup.visible:
                self._popup.popup()
            self._popup.set_loading(True)
        elif self._popup.visible:
            # In this case, the user has deleted text to less than the
            # min key length, so pop it down
            if self._source_id is not None:
                glib.source_remove(self._source_id)
                self._source_id = None
            self._popup.popdown()

    def _on_entry__activate(self, entry):
        self._popup.popdown()
        self._popup.confirm()

    def _on_entry_sensitive(self, entry, pspec):
        self._update_widgets()

    def _on_popup__item_selected(self, popup, item, fallback_to_search):
        self.set_value(self.get_object_from_item(item))
        popup.popdown()
        self.entry.grab_focus()
        glib.idle_add(self.entry.select_region, len(self.entry.get_text()), -1)

        if item is None and fallback_to_search:
            self._run_search()

    def _on_popup__create_item(self, popup):
        obj = self._run_editor(description=unicode(self.entry.get_text()))
        self.set_value(obj)

    def _on_edit_button__clicked(self, entry):
        current_obj = self.entry.read()
        obj = self._run_editor(current_obj)
        if obj:
            self.set_value(obj, force=True)


class PersonEntryGadget(QueryEntryGadget):

    PERSON_TYPE = None

    def __init__(self, entry, store, initial_value=None,
                 parent=None, run_editor=None, edit_button=None):
        country = api.sysparam.get_string('COUNTRY_SUGGESTED')
        self._company_l10n = api.get_l10n_field('company_document', country)
        self._person_l10n = api.get_l10n_field('person_document', country)

        super(PersonEntryGadget, self).__init__(
            entry, store, initial_value=initial_value,
            parent=parent, run_editor=run_editor, edit_button=edit_button)

    #
    #  QueryEntryGadget
    #

    def get_object_from_item(self, item):
        return item and self.store.find(self.PERSON_TYPE, id=item.id).one()

    def describe_item(self, person_view):
        details = []
        birth_date = (person_view.birth_date and
                      person_view.birth_date.strftime('%x'))
        for label, value in [
                (_("Phone"), person_view.phone_number),
                (_("Mobile"), person_view.mobile_number),
                (self._person_l10n.label, person_view.cpf),
                (self._company_l10n.label, person_view.cnpj),
                (_("RG"), person_view.rg_number),
                (_("Birth date"), birth_date),
                (_("Category"), getattr(person_view, 'client_category', None)),
                (_("Address"), format_address(person_view))]:
            if not value:
                continue
            details.append('%s: %s' % (label, api.escape(value)))

        name = "<big>%s</big>" % (api.escape(person_view.get_description()), )
        if details:
            short = name + '\n<span size="small">%s</span>' % (
                api.escape(', '.join(details[:1])))
            complete = name + '\n<span size="small">%s</span>' % (
                api.escape('\n'.join(details)))
        else:
            short = name
            complete = name

        return short, complete


class ClientEntryGadget(PersonEntryGadget):

    LOADING_ITEMS_TEXT = _('Loading clients...')
    NEW_ITEM_TEXT = _('Create a new client with this name...')
    NEW_ITEM_TOOLTIP = _('Create a new client')
    EDIT_ITEM_TOOLTIP = _('Edit the selected client')
    ITEM_EDITOR = ClientEditor
    PERSON_TYPE = Client
    SEARCH_CLASS = ClientSearch
    SEARCH_SPEC = ClientView
    SEARCH_COLUMNS = [ClientView.name, ClientView.fancy_name,
                      ClientView.phone_number, ClientView.mobile_number,
                      ClientView.cpf, ClientView.rg_number]


class SupplierEntryGadget(PersonEntryGadget):

    LOADING_ITEMS_TEXT = _('Loading suppliers...')
    NEW_ITEM_TEXT = _('Create a new supplier with this name...')
    NEW_ITEM_TOOLTIP = _('Create a new supplier')
    EDIT_ITEM_TOOLTIP = _('Edit the selected supplier')
    ITEM_EDITOR = SupplierEditor
    PERSON_TYPE = Supplier
    SEARCH_CLASS = SupplierSearch
    SEARCH_SPEC = SupplierView
    SEARCH_COLUMNS = [SupplierView.name, SupplierView.fancy_name,
                      SupplierView.phone_number, SupplierView.mobile_number,
                      SupplierView.cpf, SupplierView.rg_number]
