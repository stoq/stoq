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

import gobject
import gtk
from kiwi.accessor import kgetattr
from kiwi.interfaces import IValidatableProxyWidget
from kiwi.ui.objectlist import ObjectList
from kiwi.ui.widgets.combo import ProxyComboBox, ProxyComboEntry
from kiwi.ui.widgets.entry import ProxyDateEntry
from storm.info import get_cls_info

import stoq
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.countries import countries
from stoqlib.lib.diffutils import diff_lines


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
        self.output = ''

    def _add_namespace(self, namespace, prefix=''):
        for attr, value in namespace.items():
            try:
                self._items[hash(value)] = prefix + attr
            except TypeError:
                continue

    def _dump_widget(self, widget, indent=0):
        recurse = True
        line_props = []
        props = []
        extra_output = ''
        spaces = (' ' * (indent * 2))
        name = self._items.get(hash(widget), '')
        if name:
            line_props.append(name)

        parent = widget.props.parent
        if parent:
            if isinstance(parent, gtk.Box):
                (expand, fill,
                 padding, pack_type) = parent.query_child_packing(widget)
                if expand:
                    line_props.append('expand=%r' % (expand == True, ))
                if fill:
                    line_props.append('fill=%r' % (fill == True, ))
                if padding != 0:
                    line_props.append('padding=%d' % (padding, ))
                if pack_type == gtk.PACK_END:
                    line_props.append('pack-end')

        if not widget.get_visible():
            props.append('hidden')
        if not widget.get_sensitive():
            props.append('insensitive')

        if isinstance(widget, gtk.Window):
            props.append('title=%r' % (widget.get_title()))

        if isinstance(widget, gtk.Entry):
            text = widget.get_text()
            props.insert(0, repr(text))
            recurse = False
        if isinstance(widget, gtk.ToggleButton):
            if widget.get_active():
                props.append('active')
        if isinstance(widget, gtk.Button):
            lbl = widget.get_label()
            if lbl:
                props.insert(0, repr(lbl))
            recurse = False
        if isinstance(widget, gtk.Label):
            lbl = widget.get_label()
            if lbl:
                props.insert(0, repr(lbl))
            recurse = False
        if IValidatableProxyWidget.providedBy(widget):
            if (not widget.is_valid() and
                widget.get_sensitive() and
                widget.get_visible()):
                if widget.mandatory:
                    props.append('mandatory')
                else:
                    props.append('invalid')
        if isinstance(widget, (ProxyComboBox, ProxyComboEntry)):
            selected = widget.get_selected_label()
            labels = widget.get_model_strings()
            if (labels and labels[0] == 'Afghanistan' and
                sorted(labels) == sorted(countries)):
                labels = [selected,
                          '... %d more countries ...' % (len(countries) - 1)]

            for label in labels:
                line = [repr(label)]
                if label == selected:
                    line.append('selected')
                extra_output += spaces + '    item: ' + ', '.join(line) + '\n'
            recurse = False
        if isinstance(widget, ProxyDateEntry):
            props.insert(0, repr(widget.get_date()))
            recurse = False
        if isinstance(widget, ObjectList):
            # New indent is:
            #   old indentation + 'ObjectList('
            for column in widget.get_columns():
                col = []
                col.append('title=%r' % (column.title))
                if not column.visible:
                    col.append('hidden')
                if column.expand:
                    col.append('expand')
                extra_output += spaces + '    column: ' + ', '.join(col) + '\n'

            model = widget.get_model()
            for row in model:
                inst = row[0]
                cols = []
                for column in widget.get_columns():
                    cols.append(repr(kgetattr(inst, column.attribute, None)))
                extra_output += spaces + '    row: ' + ', '.join(cols) + '\n'
            recurse = False

        self.output += "%s%s(%s): %s\n" % (
            spaces,
            gobject.type_name(widget),
            ', '.join(line_props),
            ', '.join(props))
        if extra_output:
            self.output += extra_output
        if not recurse:
            return
        self._dump_children(widget, indent)

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

    def dump_editor(self, editor):
        self._add_namespace(editor.__dict__)
        self._add_namespace(editor.main_dialog.__dict__, 'main_dialog.')

        self.output += 'editor: %s\n' % (editor.__class__.__name__, )
        self._dump_widget(editor.main_dialog.get_toplevel())

    def dump_wizard(self, wizard):
        self._add_namespace(wizard.__dict__)
        step = wizard.get_current_step()
        if step:
            self._add_namespace(step.__dict__)
        self.output += 'wizard: %s\n' % (wizard.__class__.__name__, )
        self._dump_widget(wizard.get_toplevel())

    def dump_dialog(self, dialog):
        self._add_namespace(dialog.__dict__)

        self.output += 'dialog: %s\n' % (dialog.__class__.__name__, )
        self._dump_widget(dialog.get_toplevel())

    def dump_slave(self, slave):
        self._add_namespace(slave.__dict__)

        self.output += 'slave: %s\n' % (slave.__class__.__name__, )
        self._dump_widget(slave.get_toplevel())

    def dump_app(self, app):
        self._add_namespace(app.__dict__)

        self.output += 'app: %s\n' % (app.__class__.__name__, )
        self._dump_widget(app.get_toplevel())

    def dump_models(self, models):
        if not models:
            return
        self.output += '\n'
        for model in models:
            self._dump_model(model)

    def _dump_model(self, model):
        if model is None:
            self.output += 'model: None\n'
            return
        model_type = type(model)
        self.output += 'model: %s\n' % (model_type.__name__, )
        info = get_cls_info(model_type)
        for col in info.columns:
            if col.name.endswith('_id') or col.name == 'id':
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
    def _get_ui_filename(self, name):
        return os.path.join(stoq_dir, 'tests', 'ui', name + '.uitest')

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
