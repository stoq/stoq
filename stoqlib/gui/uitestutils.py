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
import os
import sys
import traceback

import gobject
import gtk
from kiwi.accessor import kgetattr
from kiwi.interfaces import IValidatableProxyWidget
from kiwi.ui.objectlist import ObjectList
from kiwi.ui.views import SlaveView
from kiwi.ui.widgets.combo import ProxyComboBox, ProxyComboEntry
from kiwi.ui.widgets.entry import ProxyDateEntry
from storm.info import get_cls_info

import stoq
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.database.testsuite import test_system_notifier
from stoqlib.gui.stockicons import register
from stoqlib.lib.countries import countries
from stoqlib.lib.diffutils import diff_lines

register()


def _get_table_packing_properties(parent, child):
    return (parent.child_get(child, 'top-attach')[0],
            parent.child_get(child, 'bottom-attach')[0],
            parent.child_get(child, 'left-attach')[0],
            parent.child_get(child, 'right-attach')[0])


class GUIDumper(object):
    """
GtkWindow(PaymentEditor):
  GtkVBox(vbox1):
    GtkHBox(hbox1, padding=6):
      Label(name_lbl): ["Name:"], pack-start
      GtkEntry(name): ["", sensitive, focus], pack-start
    GtkHBox(hbox2, padding=6):
      Label(method_lbl): ["Method:"]
      ComboEntry(method): ["Money", sensitive]
      """

    def __init__(self):
        self._items = {}
        self._slave_holders = {}
        self.output = ''

    def _add_namespace(self, obj, prefix=''):
        for attr, value in obj.__dict__.items():
            try:
                self._items[hash(value)] = prefix + attr
            except TypeError:
                continue

        if isinstance(obj, SlaveView):
            for name, slave in obj.slaves.items():
                self._add_namespace(slave)
                holder = slave.get_toplevel().get_parent()
                self._slave_holders[holder] = type(slave).__name__

    def _get_packing_properties(self, widget):
        parent = widget.props.parent
        if not parent:
            return []

        props = []
        if isinstance(parent, gtk.Box):
            (expand, fill,
             padding, pack_type) = parent.query_child_packing(widget)
            if expand:
                props.append('expand=%r' % (expand == True, ))
            if fill:
                props.append('fill=%r' % (fill == True, ))
            if padding != 0:
                props.append('padding=%d' % (padding, ))
            if pack_type == gtk.PACK_END:
                props.append('pack-end')
        return props

    def _dump_children(self, widget, indent):
        indent += 1
        if isinstance(widget, gtk.Table):
            def table_sort(a, b):
                props_a = _get_table_packing_properties(widget, a)
                props_b = _get_table_packing_properties(widget, b)
                return cmp(props_a, props_b)

            for child in sorted(widget.get_children(),
                            cmp=table_sort):
                self._dump_widget(child, indent)
        elif isinstance(widget, gtk.Container):
            for child in widget.get_children():
                self._dump_widget(child, indent)
        elif isinstance(widget, gtk.Bin):
            self._dump_widget([widget.get_child()], indent)
        if isinstance(widget, gtk.MenuItem):
            menu = widget.get_submenu()
            if menu is not None:
                self._dump_widget(menu, indent)

    def _dump_widget(self, widget, indent=0):
        if isinstance(widget, gtk.Window):
            self._dump_window(widget, indent)
        elif isinstance(widget, gtk.Entry):
            self._dump_entry(widget, indent)
        elif isinstance(widget, gtk.ToggleButton):
            self._dump_toggle_button(widget, indent)
        elif isinstance(widget, gtk.Button):
            self._dump_button(widget, indent)
        elif isinstance(widget, gtk.Label):
            self._dump_label(widget, indent)
        elif isinstance(widget, (ProxyComboBox, ProxyComboEntry)):
            self._dump_proxy_combo(widget, indent)
        elif isinstance(widget, ProxyDateEntry):
            self._dump_proxy_date_entry(widget, indent)
        elif isinstance(widget, gtk.IconView):
            self._dump_iconview(widget, indent)
        elif isinstance(widget, ObjectList):
            self._dump_objectlist(widget, indent)
        elif isinstance(widget, gtk.EventBox):
            self._dump_event_box(widget, indent)
        else:
            self._write_widget(widget, indent)
            self._dump_children(widget, indent)

    def _write_widget(self, widget, indent=0, props=None, extra=[]):
        line_props = []
        name = self._items.get(hash(widget), '')
        if name:
            line_props.append(name)

        line_props.extend(self._get_packing_properties(widget))

        spaces = (' ' * (indent * 2))
        if not props:
            props = []

        if not widget.get_visible():
            props.append('hidden')
        if not widget.get_sensitive():
            props.append('insensitive')

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
            gobject.type_name(widget),
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
        self._write_widget(entry, indent, [text])

    def _dump_label(self, label, indent):
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
        for column in objectlist.get_columns():
            col = []
            col.append('title=%r' % (column.title))
            if not column.visible:
                col.append('hidden')
            if column.expand:
                col.append('expand')
            extra.append('column: ' + ', '.join(col))

        model = objectlist.get_model()
        for row in model:
            inst = row[0]
            cols = []
            for column in objectlist.get_columns():
                cols.append(repr(kgetattr(inst, column.attribute, None)))
            extra.append('row: ' + ', '.join(cols))
        self._write_widget(objectlist, indent, extra=extra)

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


stoq_dir = os.path.dirname(os.path.dirname(stoq.__file__))


class GUITest(DomainTest):
    def setUp(self):
        self._unhandled_exceptions = []
        self._old_hook = sys.excepthook
        sys.excepthook = self._except_hook
        test_system_notifier.reset()
        DomainTest.setUp(self)

    def tearDown(self):
        sys.excepthook = self._old_hook
        DomainTest.tearDown(self)

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
        return os.path.join(stoq_dir, 'tests', 'ui', name + '.uitest')

    def click(self, button):
        """Simulates a click on a button.
        This verifies that the button is clickable (visible and sensitive) and
        emits the clicked signal
        """
        if not isinstance(button, gtk.Button):
            raise TypeError("%r must be a button" % (button, ))

        if not button.get_visible():
            self.fail("button is not visible")
            return

        if not button.get_sensitive():
            self.fail("button is not sensitive")
            return

        button.clicked()

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
            value = getattr(dialog, attr)
            # If the widget is sensitive, we also expect it to be visible
            if not value.get_sensitive() or not value.get_visible():
                self.fail("%s.%s should be sensitive" % (
                    dialog.__class__.__name__, attr))

    def assertNotSensitive(self, dialog, attributes):
        for attr in attributes:
            value = getattr(dialog, attr)
            if value.get_sensitive():
                self.fail("%s.%s should not be sensitive" % (
                    dialog.__class__.__name__, attr))

    def assertNotVisible(self, dialog, attributes):
        for attr in attributes:
            value = getattr(dialog, attr)
            if value.get_visible():
                self.fail("%s.%s should not be visible" % (
                    dialog.__class__.__name__, attr))

    def check_wizard(self, wizard, ui_test_name, models=[], ignores=[]):
        dumper = GUIDumper()
        dumper.dump_wizard(wizard)
        dumper.dump_models(models)
        self._check_filename(dumper, ui_test_name, ignores)

    def check_editor(self, editor, ui_test_name, models=[], ignores=[]):
        dumper = GUIDumper()
        dumper.dump_editor(editor)
        dumper.dump_models(models)
        self._check_filename(dumper, ui_test_name, ignores)

    def check_dialog(self, dialog, ui_test_name, models=[], ignores=[]):
        dumper = GUIDumper()
        dumper.dump_dialog(dialog)
        dumper.dump_models(models)
        self._check_filename(dumper, ui_test_name, ignores)

    def check_slave(self, slave, ui_test_name, models=[], ignores=[]):
        dumper = GUIDumper()
        dumper.dump_slave(slave)
        dumper.dump_models(models)
        self._check_filename(dumper, ui_test_name, ignores)

    def _check_filename(self, dumper, ui_test_name, ignores=[]):
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

        filename = self._get_ui_filename(ui_test_name)
        if not os.path.exists(filename):
            open(filename, 'w').write(text)
            return

        lines = [(line + '\n') for line in text.split('\n')][:-1]
        expected = open(filename).readlines()
        difference = diff_lines(expected,
                                lines,
                                short=filename[len(stoq_dir) + 1:])
        if difference:
            self.fail('ui test %s failed:\n%s' % (
                ui_test_name, difference))
