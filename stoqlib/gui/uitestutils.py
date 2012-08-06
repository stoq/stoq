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

import os
import pprint

import gobject
import gtk
from kiwi.ui.objectlist import ObjectList
from kiwi.ui.widgets.combo import ProxyComboBox, ProxyComboEntry
from kiwi.ui.widgets.entry import ProxyDateEntry

import stoq
from stoqlib.domain.test.domaintest import DomainTest
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
            elif isinstance(parent, gtk.Table):
                table_props = _get_table_packing_properties(parent, widget)
                line_props.append('%d %d %d %d' % table_props)

        if not widget.get_visible():
            props.append('hidden')
        if widget.get_sensitive():
            props.append('sensitive')
        if isinstance(widget, gtk.Entry):
            text = widget.get_text()
            props.insert(0, repr(text))
            recurse = False
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
        if isinstance(widget, (ProxyComboBox, ProxyComboEntry)):
            props.insert(0, repr(widget.get_selected_data()))
            recurse = False
        if isinstance(widget, ProxyDateEntry):
            props.insert(0, repr(widget.get_date()))
            recurse = False
        if isinstance(widget, ObjectList):
            # New indent is:
            #   old indentation + 'ObjectList('
            rows_indent = (indent * 2) + len(gobject.type_name(widget) + '(')

            def x(a, b):
                return cmp(repr(a), repr(b))
            props.insert(0, pprint.pformat(
                list(sorted(widget, cmp=x)),
                indent=rows_indent))
            recurse = False

        self.output += "%s%s(%s): %s\n" % (
            (' ' * (indent * 2)),
            gobject.type_name(widget),
            ', '.join(line_props),
            ', '.join(props))

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

        self._dump_widget(editor.main_dialog.get_toplevel())


class GUITest(DomainTest):
    def _get_ui_filename(self, name):
        return os.path.join(
            os.path.dirname(os.path.dirname(stoq.__file__)),
            'tests', 'ui', name + '.uitest')

    def assertSensitive(self, dialog, attributes):
        for attr in attributes:
            value = getattr(dialog, attr)
            if not value.get_sensitive():
                self.fail("%s.%s should be sensitive" % (
                    dialog.__class__.__name__, attr))

    def assertNotSensitive(self, dialog, attributes):
        for attr in attributes:
            value = getattr(dialog, attr)
            if value.get_sensitive():
                self.fail("%s.%s should not be sensitive" % (
                    dialog.__class__.__name__, attr))

    def check_editor(self, editor, ui_test_name, ignores=[]):
        dumper = GUIDumper()
        dumper.dump_editor(editor)

        text = dumper.output
        for ignore in ignores:
            text = text.replace(ignore, '%% FILTERED BY UNITTEST %%')

        filename = self._get_ui_filename(ui_test_name)
        if not os.path.exists(filename):
            open(filename, 'w').write(text)
            return

        lines = [(line + '\n') for line in text.split('\n')][:-1]
        expected = open(filename).readlines()
        difference = diff_lines(expected,
                                lines)
        if difference:
            self.fail('ui test %s failed:\n%s' % (
                ui_test_name, difference))
