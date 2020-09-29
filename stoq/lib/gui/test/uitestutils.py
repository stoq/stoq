# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

import datetime
import functools
import os
import re
import sys
import traceback

from gi.repository import Gtk, GObject, Gio
from kiwi.interfaces import IValidatableProxyWidget
from kiwi.ui.objectlist import ObjectList, ObjectTree
from kiwi.ui.views import SlaveView
from kiwi.ui.widgets.combo import ProxyComboBox, ProxyComboEntry
from kiwi.ui.widgets.entry import ProxyDateEntry
from stoqlib.lib.objutils import cmp
from storm.info import get_cls_info

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.database.testsuite import test_system_notifier
from stoq.lib.gui.actions.base import BaseActions
from stoq.lib.gui.search.searchresultview import SearchResultListView
from stoq.lib.gui.stockicons import register
from stoqlib.lib.countries import countries
from stoqlib.lib.diffutils import diff_lines
from stoqlib.lib.unittestutils import get_tests_datadir

register()

_UUID_RE = re.compile("'[a-f0-9]{8}-"
                      "[a-f0-9]{4}-"
                      "[a-f0-9]{4}-"
                      "[a-f0-9]{4}-"
                      "[a-f0-9]{12}'")


def _get_table_packing_properties(parent, child):
    return (parent.child_get(child, 'top-attach')[0],
            parent.child_get(child, 'bottom-attach')[0],
            parent.child_get(child, 'left-attach')[0],
            parent.child_get(child, 'right-attach')[0])


class GUIDumper(object):
    """A class used to dump the state of a widget tree and serialize
    it into a string that can be saved on disk.
    """

    def __init__(self):
        self._items = {}
        self._slave_holders = {}
        self.output = ''
        self.failures = []

    def _add_namespace(self, obj, prefix=''):
        for attr in dir(obj):
            try:
                value = getattr(obj, attr)
            except RuntimeError:
                # This happens in 3 tests when attr is bin
                continue
            try:
                self._items[value] = prefix + attr
            except TypeError:
                continue

        if isinstance(obj, SlaveView):
            for name, slave in obj.slaves.items():
                self._add_namespace(slave)
                holder = slave.get_toplevel().get_parent()
                self._slave_holders[holder] = type(slave).__name__

    def _get_packing_properties(self, widget):
        # FIXME: Workaround for GtkWindow::parent property
        #        on PyGTK for natty
        if isinstance(widget, Gtk.Window):
            return []

        props = []
        if (GObject.type_name(widget).endswith('Box') and
                isinstance(widget, Gtk.Orientable)):
            orientation = {
                Gtk.Orientation.HORIZONTAL: 'horizontal',
                Gtk.Orientation.VERTICAL: 'vertical',
            }[widget.get_orientation()]
            props.append('orientation={}'.format(orientation))

        parent = widget.props.parent
        if not parent:
            return props

        if isinstance(parent, Gtk.Box):
            (expand, fill,
             padding, pack_type) = parent.query_child_packing(widget)
            if expand:
                props.append('expand=%r' % (bool(expand), ))
            if fill:
                props.append('fill=%r' % (bool(fill), ))
            if padding != 0:
                props.append('padding=%d' % (padding, ))
            if pack_type == Gtk.PackType.END:
                props.append('pack-end')
        return props

    def _dump_children(self, widget, indent):
        indent += 1
        if isinstance(widget, Gtk.Table):
            def table_sort(a, b):
                props_a = _get_table_packing_properties(widget, a)
                props_b = _get_table_packing_properties(widget, b)
                return cmp(props_a, props_b)

            for child in sorted(widget.get_children(),
                                key=functools.cmp_to_key(table_sort)):
                self._dump_widget(child, indent)
        elif isinstance(widget, Gtk.Container):
            for child in widget.get_children():
                self._dump_widget(child, indent)
        elif isinstance(widget, Gtk.Bin):
            self._dump_widget([widget.get_child()], indent)
        if isinstance(widget, Gtk.MenuItem):
            menu = widget.get_submenu()
            if menu is not None:
                self._dump_widget(menu, indent)

    def _dump_widget(self, widget, indent=0):
        if widget is None:
            return

        if isinstance(widget, Gtk.Window):
            self._dump_window(widget, indent)
        elif isinstance(widget, Gtk.Entry):
            self._dump_entry(widget, indent)
        elif isinstance(widget, Gtk.ModelButton):
            self._dump_model_button(widget, indent)
        elif isinstance(widget, Gtk.MenuButton):
            self._dump_menu_button(widget, indent)
        elif isinstance(widget, Gtk.ToggleButton):
            self._dump_toggle_button(widget, indent)
        elif isinstance(widget, Gtk.Button):
            self._dump_button(widget, indent)
        elif isinstance(widget, Gtk.Label):
            self._dump_label(widget, indent)
        elif isinstance(widget, (ProxyComboBox, ProxyComboEntry)):
            self._dump_proxy_combo(widget, indent)
        elif isinstance(widget, ProxyDateEntry):
            self._dump_proxy_date_entry(widget, indent)
        elif isinstance(widget, Gtk.IconView):
            self._dump_iconview(widget, indent)
        elif isinstance(widget, ObjectList):
            self._dump_objectlist(widget, indent)
        elif isinstance(widget, Gtk.EventBox):
            self._dump_event_box(widget, indent)
        elif isinstance(widget, Gtk.MenuItem):
            self._dump_menu_item(widget, indent)
        elif isinstance(widget, Gtk.ToolItem):
            self._dump_tool_item(widget, indent)
        else:
            self._write_widget(widget, indent)
            self._dump_children(widget, indent)

    def _is_interactive_widget(self, widget):
        # FIXME: Add more widgets, but needs a careful audit
        return isinstance(widget, Gtk.Entry)

    def _write_widget(self, widget, indent=0, props=None, extra=None):
        extra = extra or []

        line_props = []
        name = self._items.get(widget, '')

        # FIXME python3: There're 2 tests that use SaleWithToolbarSearch that
        # are getting the name as 'results' or 'sales'. Idk what exactly is
        # happening in _add_namespace...
        if isinstance(widget, SearchResultListView) and name == 'sales':
            name = 'results'

        if name:
            line_props.append(name)

        line_props.extend(self._get_packing_properties(widget))

        spaces = (' ' * (indent * 2))
        if not props:
            props = []

        g_name = GObject.type_name(widget)
        if g_name in ['GtkHBox', 'GtkVBox']:
            g_name = 'GtkBox'
        elif g_name in ['GtkHButtonBox', 'GtkVButtonBox']:
            g_name = 'GtkButtonBox'

        if not widget.get_visible():
            props.append('hidden')
        if not widget.get_sensitive():
            props.append('insensitive')

        if (widget.get_sensitive() and
                widget.get_visible() and
                not widget.get_can_focus() and
                self._is_interactive_widget(widget)):
            props.append('unfocusable')
            fmt = "%s %s is not focusable"
            self.failures.append(fmt % (g_name,
                                        self._items.get(widget,
                                                        '???')))

        if IValidatableProxyWidget.providedBy(widget):
            if (not widget.is_valid() and
                    widget.get_sensitive() and
                    widget.get_visible()):
                if widget.mandatory:
                    props.append('mandatory')
                else:
                    props.append('invalid')

        if props:
            prop_lines = ' ' + ', '.join(props)
        else:
            prop_lines = ''
        self.output += "%s%s(%s):%s\n" % (
            spaces,
            g_name,
            ', '.join(line_props),
            prop_lines)
        spaces = (' ' * ((indent + 1) * 2))
        for line in extra:
            self.output += spaces + line + '\n'

    # Gtk+

    def _dump_window(self, window, indent):
        props = ['title=%r' % (window.get_title())]
        self._write_widget(window, indent, props)
        self._dump_children(window, indent)

    def _dump_event_box(self, eventbox, indent):
        slave_name = self._slave_holders.get(eventbox)
        props = []
        if slave_name:
            props.append('slave %s is attached' % (slave_name, ))

        self._write_widget(eventbox, indent, props)
        self._dump_children(eventbox, indent)

    def _dump_button(self, button, indent, props=None):
        if props is None:
            props = []
        label = button.get_label()
        if label:
            props.insert(0, repr(label))
        self._write_widget(button, indent, props)

    def _dump_entry(self, entry, indent):
        text = repr(entry.get_text())
        props = [text]
        if not entry.get_editable():
            props.append('ineditable')
        if isinstance(entry, Gtk.SpinButton):
            if entry.props.wrap:
                props.append('wrappable')

        self._write_widget(entry, indent, props)

    def _dump_label(self, label, indent):
        if (isinstance(label, Gtk.AccelLabel) and
                isinstance(label.get_parent(), Gtk.MenuItem)):
            return

        props = []
        lbl = label.get_label()
        if lbl:
            props.append(repr(lbl))
        self._write_widget(label, indent, props)

    def _dump_toggle_button(self, toggle, indent):
        props = []
        if toggle.get_active():
            props.append('active')
        self._dump_button(toggle, indent, props)

    def _dump_menu_item(self, menuitem, indent):
        # GtkUIManager creates plenty of invisible separators
        if (isinstance(menuitem, Gtk.SeparatorMenuItem) and
                not menuitem.get_visible()):
            return

        # GtkUIManager creates empty items at the end of lists
        if (isinstance(menuitem, Gtk.MenuItem) and
                not menuitem.get_visible() and
                not menuitem.get_sensitive() and
                menuitem.get_label() == 'Empty'):
            return

        # Skip tearoff menus
        if (isinstance(menuitem, Gtk.TearoffMenuItem) and
                not menuitem.get_visible()):
            return

        props = []
        label = menuitem.get_label()
        if (isinstance(menuitem, Gtk.ImageMenuItem) and
                menuitem.get_use_stock()):
                props.append('stock=%r' % (label, ))
        elif label:
            props.append(repr(label))

        self._write_widget(menuitem, indent, props)
        self._dump_children(menuitem, indent)

    def _dump_tool_item(self, toolitem, indent):
        # GtkUIManager creates plenty of invisible separators
        if (isinstance(toolitem, Gtk.SeparatorToolItem) and
                not toolitem.get_visible()):
            return

        props = []
        if isinstance(toolitem, Gtk.ToolButton):
            label = toolitem.get_label()
            if label:
                props.append(repr(label))

        self._write_widget(toolitem, indent, props)

        if isinstance(toolitem, Gtk.MenuToolButton):
            menu = toolitem.get_menu()
            if menu:
                self._dump_widget(menu, indent + 2)

    def _dump_menu_button(self, widget, indent):
        self._write_widget(widget, indent, [])
        popover = widget.get_popover()
        self._dump_widget(popover, indent + 2)

    def _dump_model_button(self, button, indent):
        self._write_widget(button, indent, [button.props.text])

    def _dump_iconview(self, iconview, indent):
        extra = []
        model = iconview.get_model()
        markup_id = iconview.get_markup_column()
        text_id = iconview.get_text_column()
        pixbuf_id = iconview.get_pixbuf_column()
        for row in model:
            cols = []
            if markup_id != -1:
                cols.append('markup: ' + row[markup_id])
            if text_id != -1:
                cols.append('text: ' + row[text_id])
            if pixbuf_id != -1:
                stock_id = getattr(row[pixbuf_id], 'stock_id', None)
                if stock_id:
                    cols.append('stock: ' + stock_id)

            extra.append(', '.join(cols))
        self._write_widget(iconview, indent, extra=extra)

    # Kiwi

    def _dump_proxy_date_entry(self, dateentry, indent):
        props = [repr(dateentry.get_date())]
        self._write_widget(dateentry, indent, props)

    def _dump_proxy_combo(self, combo, indent):
        extra = []
        selected = combo.get_selected_label()
        labels = combo.get_model_strings()
        if (labels and labels[0] == 'Afghanistan' and
                sorted(labels) == sorted(countries)):
            labels = [selected,
                      '... %d more countries ...' % (len(countries) - 1)]

        for label in labels:
            line = [repr(label)]
            if label == selected:
                line.append('selected')
            extra.append('item: ' + ', '.join(line))
        self._write_widget(combo, indent, extra=extra)

    def _dump_objectlist(self, objectlist, indent):
        extra = []
        is_tree = isinstance(objectlist, ObjectTree)

        for column in objectlist.get_columns():
            col = []
            col.append('title=%r' % (column.title))
            if not column.visible:
                col.append('hidden')
            if column.expand:
                col.append('expand')
            extra.append('column: ' + ', '.join(col))

        def append_row(row, extra_indent=0):
            inst = row[0]
            cols = []
            cols = [repr(col.get_attribute(inst, col.attribute, None)) for
                    col in objectlist.get_columns()]
            extra.append("%srow: %s" % (
                ' ' * extra_indent, ', '.join(cols)))

            if is_tree:
                extra_indent = extra_indent + 2
                for child in row.iterchildren():
                    append_row(child, extra_indent=extra_indent)

        model = objectlist.get_model()
        for row in model:
            append_row(row)

        self._write_widget(objectlist, indent, extra=extra)

    def dump_widget(self, widget):
        self._add_namespace(widget)

        self.output += 'widget: %s\n' % (widget.__class__.__name__, )
        self._dump_widget(widget)

    def dump_editor(self, editor):
        self._add_namespace(editor)
        self._add_namespace(editor.main_dialog, 'main_dialog.')

        self.output += 'editor: %s\n' % (editor.__class__.__name__, )
        self._dump_widget(editor.main_dialog.get_toplevel())

    def dump_wizard(self, wizard):
        self._add_namespace(wizard)
        step = wizard.get_current_step()
        if step:
            self._add_namespace(step, 'step.')
        self.output += 'wizard: %s\n' % (wizard.__class__.__name__, )
        self._dump_widget(wizard.get_toplevel())

    def dump_dialog(self, dialog):
        self._add_namespace(dialog)

        self.output += 'dialog: %s\n' % (dialog.__class__.__name__, )
        self._dump_widget(dialog.get_toplevel())

    def dump_slave(self, slave):
        self._add_namespace(slave)

        self.output += 'slave: %s\n' % (slave.__class__.__name__, )
        self._dump_widget(slave.get_toplevel())

    def dump_search(self, search):
        self._add_namespace(search)

        self.output += 'search: %s\n' % (search.__class__.__name__, )
        self._dump_widget(search.get_toplevel())

    def dump_app(self, app):
        self._add_namespace(app)

        self.output += 'app: %s\n' % (app.__class__.__name__, )
        self._dump_widget(app.get_toplevel())

    def dump_models(self, models):
        if not models:
            return
        self.output += '\n'
        counter = 1
        ns = {}
        for model in models:
            model_name = '%s<%d>' % (type(model).__name__,
                                     counter)
            ns[model] = model_name
            counter += 1
        for model in models:
            self._dump_model(ns, model)

    def _dump_model(self, ns, model):
        if model is None:
            self.output += 'model: None\n'
            return
        self.output += 'model: %s\n' % (ns[model], )
        info = get_cls_info(type(model))
        for col in info.columns:
            if col.name == 'id' or col.name == 'identifier':
                continue
            if col.name.endswith('_id'):
                value = getattr(model, col.name[:-3], None)
                if value in ns:
                    self.output += '  %s: %s\n' % (col.name, ns[value])
                continue

            value = getattr(model, col.name, None)
            if isinstance(value, datetime.datetime):
                # Strip hours/minutes/seconds so today() works
                value = datetime.datetime(value.year,
                                          value.month,
                                          value.day)

            self.output += '  %s: %r\n' % (col.name, value)
        self.output += '\n'


# FIXME: To be able to create ui tests outside stoq, we need to be able
# to get tests data dir from there. Maybe we should use
# provide_utility/get_utility?
stoq_dir = get_tests_datadir('ui')


class GUITest(DomainTest):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        from stoqlib.database.runtime import new_store
        self.store = new_store()
        self.fake.set_store(self.store)
        self.set_store(self.store)

        self._unhandled_exceptions = []
        self._old_hook = sys.excepthook
        sys.excepthook = self._except_hook
        test_system_notifier.reset()
        DomainTest.setUp(self)

    def tearDown(self):
        self.store.close()
        self.fake.set_store(None)
        self.clear()

        sys.excepthook = self._old_hook

        messages = test_system_notifier.reset()
        if messages:
            self.fail("Unhandled messages: %r, use @mock.patch()" % (
                messages, ))

        if self._unhandled_exceptions:
            self.fail("Unhandled exceptions: %r" % (
                self._unhandled_exceptions))

    def _except_hook(self, exc_type, exc_value, exc_traceback):
        self._unhandled_exceptions.append((exc_type, exc_value, exc_traceback))
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    def _get_ui_filename(self, name):
        return os.path.join(stoq_dir, name + '.uitest')

    def click(self, button):
        """Simulates a click on a button.
        This verifies that the button is clickable (visible and sensitive) and
        emits the clicked signal
        """
        if not isinstance(button, Gtk.Button):
            raise TypeError("%r must be a button" % (button, ))

        if not button.get_visible():
            self.fail("button is not visible")
            return

        if not button.get_sensitive():
            self.fail("button is not sensitive")
            return

        button.clicked()

    def activate(self, widget):
        """Simulates activation on a widget
        This verifies that the button is activatable (visible and sensitive) and
        emits the activate signal
        """
        if not isinstance(widget, (Gtk.Action, Gtk.Widget, Gio.Action)):
            raise TypeError("%r must be an action or a widget" % (widget, ))

        if not isinstance(widget, Gio.Action) and not widget.get_visible():
            self.fail("widget is not visible")
            return

        if isinstance(widget, Gio.Action):
            if not widget.get_enabled():
                self.fail("widget is not sensitive")
                return
        else:
            if not widget.get_sensitive():
                self.fail("widget is not sensitive")
                return

        widget.activate()

    def assertInvalid(self, dialog, attributes):
        for attr in attributes:
            value = getattr(dialog, attr)
            if value.is_valid():
                self.fail("%s.%s should be invalid" % (
                    dialog.__class__.__name__, attr))

    def assertValid(self, dialog, attributes):
        for attr in attributes:
            value = getattr(dialog, attr)
            if not value.is_valid():
                self.fail("%s.%s should be valid" % (
                    dialog.__class__.__name__, attr))

    def assertSensitive(self, dialog, attributes):
        for attr in attributes:
            if isinstance(dialog, BaseActions):
                value = dialog.get_action(attr)
            else:
                value = getattr(dialog, attr)

            # If the widget is sensitive, we also expect it to be visible
            if isinstance(value, Gio.Action):
                if not value.get_enabled():
                    self.fail("%s.%s should be sensitive" % (
                        dialog.__class__.__name__, attr))
                continue
            if not value.get_sensitive() or not value.get_visible():
                self.fail("%s.%s should be sensitive" % (
                    dialog.__class__.__name__, attr))

    def assertNotSensitive(self, dialog, attributes):
        for attr in attributes:
            value = getattr(dialog, attr)
            if isinstance(value, Gio.Action):
                if value.get_enabled():
                    self.fail("%s.%s should not be sensitive" % (
                        dialog.__class__.__name__, attr))
                continue
            if value.get_sensitive():
                self.fail("%s.%s should not be sensitive" % (
                    dialog.__class__.__name__, attr))

    def assertVisible(self, dialog, attributes):
        for attr in attributes:
            value = getattr(dialog, attr)
            if not value.get_visible():
                self.fail("%s.%s should be visible" % (
                    dialog.__class__.__name__, attr))

    def assertNotVisible(self, dialog, attributes):
        for attr in attributes:
            value = getattr(dialog, attr)
            if value.get_visible():
                self.fail("%s.%s should not be visible" % (
                    dialog.__class__.__name__, attr))

    def check_widget(self, widget, ui_test_name, models=None, ignores=None):
        models = models or []
        ignores = ignores or []

        dumper = GUIDumper()
        dumper.dump_widget(widget)
        dumper.dump_models(models)
        self.check_filename(dumper, ui_test_name, ignores)

    def check_wizard(self, wizard, ui_test_name, models=None, ignores=None):
        models = models or []
        ignores = ignores or []

        dumper = GUIDumper()
        dumper.dump_wizard(wizard)
        dumper.dump_models(models)
        self.check_filename(dumper, ui_test_name, ignores)

    def check_editor(self, editor, ui_test_name, models=None, ignores=None):
        models = models or []
        ignores = ignores or []

        dumper = GUIDumper()
        dumper.dump_editor(editor)
        dumper.dump_models(models)
        self.check_filename(dumper, ui_test_name, ignores)

    def check_dialog(self, dialog, ui_test_name, models=None, ignores=None):
        models = models or []
        ignores = ignores or []

        dumper = GUIDumper()
        dumper.dump_dialog(dialog)
        dumper.dump_models(models)
        self.check_filename(dumper, ui_test_name, ignores)

    def check_slave(self, slave, ui_test_name, models=None, ignores=None):
        models = models or []
        ignores = ignores or []

        dumper = GUIDumper()
        dumper.dump_slave(slave)
        dumper.dump_models(models)
        self.check_filename(dumper, ui_test_name, ignores)

    def check_search(self, search, ui_test_name, models=None, ignores=None):
        models = models or []
        ignores = ignores or []

        dumper = GUIDumper()
        dumper.dump_search(search)
        dumper.dump_models(models)
        self.check_filename(dumper, 'search-' + ui_test_name, ignores)

    def check_app(self, app, ui_test_name, models=None, ignores=None):
        models = models or []
        ignores = ignores or []

        dumper = GUIDumper()
        dumper.dump_app(app)
        dumper.dump_models(models)
        self.check_filename(dumper, 'app-' + ui_test_name, ignores)

    def check_filename(self, dumper, ui_test_name, ignores=None):
        ignores = ignores or []

        text = dumper.output
        for ignore in ignores:
            text = text.replace(ignore, '%% FILTERED BY UNITTEST %%')

        today = datetime.date.today()
        text = text.replace(repr(today), 'date.today()')
        text = text.replace(today.strftime('%x'), "YYYY-MM-DD")
        text = text.replace(today.strftime('%Y-%m-%d'), "YYYY-MM-DD")
        text = text.replace(
            repr(datetime.datetime(today.year, today.month, today.day)),
            'datetime.today()')

        text = _UUID_RE.sub("uuid.uuid()", text)

        if os.environ.get('STOQ_USE_GI', '') == '3.0':
            # These are internal changes of GtkDialog which we
            # don't want to see.
            # They can safely be removed when we drop PyGTK support

            # GtkHButtonBox doesn't exist any longer and we don't
            # use GtkVButtonBox
            text = text.replace('GtkButtonBox', 'GtkHButtonBox')
            text = text.replace(
                'GtkBox(PluggableWizard-vbox',
                'GtkVBox(PluggableWizard-vbox')
            text = text.replace(
                'GtkBox(main_dialog._main_vbox',
                'GtkVBox(main_dialog._main_vbox')
            text = text.replace(
                'GtkBox(_main_vbox',
                'GtkVBox(_main_vbox')
            text = text.replace('stoq+lib+gicompat+', 'Gtk')

        filename = self._get_ui_filename(ui_test_name)
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write(text)

            self._check_failures(dumper)
            return

        lines = [(line + '\n') for line in text.split('\n')][:-1]
        with open(filename) as f:
            expected = f.readlines()
        difference = diff_lines(expected,
                                lines,
                                short=filename[len(stoq_dir) + 1:])

        # Allow users to easily update uitests by running, for example:
        #   $ STOQ_REPLACE_UITESTS=1 make check-failed
        replace_tests = os.environ.get('STOQ_REPLACE_UITESTS', False)
        if difference and replace_tests:
            print("\n ** The test %s differed, but being replaced since "
                  "STOQ_REPLACE_UITESTS is set **" % filename)
            with open(filename, 'w') as f:
                f.write(text)
        elif difference:
            self.fail('ui test %s failed:\n%s' % (
                ui_test_name, difference))

        self._check_failures(dumper)

    def _check_failures(self, dumper):
        # Make sure unfocused is never saved, this should happen after
        # the difference above, since that is a much more useful error message
        # (with a complete diff) rather than just an error message
        if dumper.failures:
            self.fail(dumper.failures)
