# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2016 Async Open Source <http://www.async.com.br>
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
"""Dialog to mass edit value of database objects

This will allow the user to choose the field he wants to mass update, the rule
for the update and set some parameters depending on those rules. For instance:

  Price / Cost (Decimal)
    - Multiply value of [   |v] by [    ]
    - Add value of [   |v] with [    ]
    - Set to [   ]
  Description / Code / Barcode / Others (String)
    - Replace   [    ] by [    ]
    - Append    [    ]
    - Prepend   [    ]
    - Set to (if not unique)
  Category (Reference)
    - Set to    [   |v]
"""

from decimal import Decimal

import gtk
import pango
from kiwi import ValueUnset
from kiwi.currency import currency
from kiwi.datatypes import converter
from kiwi.ui.objectlist import Column
from kiwi.ui.widgets.combo import ProxyComboBox
from kiwi.ui.widgets.entry import ProxyEntry

from stoqlib.gui.dialogs.progressdialog import ProgressDialog
from stoqlib.gui.search.searchcolumns import SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.lib.message import marker
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


#
#   Operations
#

class Operation(gtk.HBox):
    """Base class for an operation

    An operation has some parameters (created by subclasses at will) and should
    return a new value that will update a field in the objects.
    """

    def __init__(self, store, field, other_fields):
        self._store = store
        self._field = field
        gtk.HBox.__init__(self, spacing=6)
        self.setup(other_fields)
        self.show_all()

    def set_field(self, field):
        self._field = field

    def add_label(self, label):
        """Add a label to self
        """
        label = gtk.Label(label)
        self.pack_start(label, False, False)
        return label

    def add_entry(self, data_type):
        """Add a entry with the specified data_type

        The user will be able to provide any information in the entry that
        should be used by this operation (for instance, a number do multiply a
        value for or a string to replace a value for)
        """
        entry = ProxyEntry(data_type=data_type)
        self.pack_start(entry, False, False)
        return entry

    def add_combo(self, data=None):
        """Add a combo for selecting an option"""
        combo = ProxyComboBox()
        self.pack_start(combo, False, False)
        if data:
            combo.prefill(data)
        return combo

    def add_field_combo(self, fields):
        """Adds a combo for selecting another field.

        The other field should be used as a reference value for the operation.
        for instance: a value that should be multiplied by or added to.
        """
        combo = self.add_combo()
        for f in fields:
            combo.append_item(f.label, f)
        return combo

    def setup(self):  # pragma nocover
        """Setup this operation.

        Subclasses should override this method and add other fields that the
        user can set how the operation should work.
        """
        raise NotImplementedError()

    def get_new_value(self, item):  # pragma nocover
        """Returns the new value for the item

        Subclasses must override this method and return a new value for the
        object field
        """
        raise NotImplementedError()

    def apply_operation(self, item):
        value = self.get_new_value(item)
        if value is not ValueUnset:
            self._field.set_new_value(item, value)


class MultiplyOperation(Operation):
    """An operation that multiplies a field with a value"""

    label = _('Multiply value of')
    middle_label = _('by')

    def setup(self, other_fields):
        self.combo = self.add_field_combo(other_fields)
        self.add_label(self.middle_label)
        self.entry = self.add_entry(Decimal)

    def get_new_value(self, item):
        multiplier = self.entry.validate()
        if multiplier is ValueUnset:
            return ValueUnset
        other_field = self.combo.get_selected()
        old_value = other_field.get_value(item)
        return old_value * multiplier


class AddOperation(MultiplyOperation):
    """An operation that adds a field with a value"""

    label = _('Add value of')
    middle_label = _('with')

    def get_new_value(self, item):
        value = self.entry.validate()
        if value is ValueUnset:
            return ValueUnset
        other_field = self.combo.get_selected()
        old_value = other_field.get_value(item)
        return old_value + value


class DivideOperation(MultiplyOperation):
    """An operation that divides a field by a value"""

    label = _('Divide value of')
    middle_label = _('by')

    def get_new_value(self, item):
        divider = self.entry.validate()
        if divider is ValueUnset:
            return ValueUnset
        other_field = self.combo.get_selected()
        old_value = other_field.get_value(item)
        return old_value / divider


class SetValueOperation(Operation):
    """An operation that sets a field to a specifc value.

    This works for both strings and numerical values
    """

    label = _('Set value to')

    def setup(self, other_fields):
        self.entry = self.add_entry(self._field.data_type)

    def get_new_value(self, item):
        value = self.entry.validate()
        if value is ValueUnset:
            return ValueUnset
        return value


class ReplaceOperation(Operation):
    """An operation that replaces a string by another one"""
    label = _('Replace')

    def setup(self, other_fields):
        self.one_entry = self.add_entry(unicode)
        self.add_label(_('by'))
        self.other_entry = self.add_entry(unicode)

    def get_new_value(self, item):
        old_value = self._field.get_value(item)
        return old_value.replace(self.one_entry.read(), self.other_entry.read())


class SetObjectValueOperation(Operation):
    """An operation that sets a field to a specifc value.

    This works only for object values.
    """

    label = _('Set value to')

    def setup(self, other_fields):
        table = self._field._reference_class
        data = self._store.find((self._field.get_search_spec(), table))
        self.combo = self.add_combo([(_('Erase value'), None)] + list(data))

    def get_new_value(self, item):
        return self.combo.read()


#
#   Field Editors
#

class Editor(gtk.HBox):
    """Base class for field editors

    Subclasses must define a list of operations and a datatype
    """

    operations = []
    data_type = None

    def __init__(self, store, field, other_fields):
        """
        :param store: a storm store if its needed
        :param field: the field that is being edited
        :param other_fields: other fields available for math operations
        """
        assert len(self.operations)

        self._store = store
        self._other_fields = other_fields
        self._oper = None
        self._field = field
        gtk.HBox.__init__(self, spacing=6)
        self.operations_combo = ProxyComboBox()
        self.pack_start(self.operations_combo)
        self.operations_combo.connect('changed', self._on_operation_changed)
        for oper in self.operations:
            self.operations_combo.append_item(oper.label, oper)
        self.operations_combo.select(self.operations[0])
        self.show_all()

    def set_field(self, field):
        assert field.data_type == self.data_type
        self._field = field
        self._oper.set_field(field)

    def _on_operation_changed(self, combo):
        if self._oper is not None:
            # Remove previous operation
            self.remove(self._oper)

        self._oper = combo.get_selected()(self._store, self._field,
                                          self._other_fields)
        self.pack_start(self._oper)

    def apply_operation(self, item):
        return self._oper.apply_operation(item)


class DecimalEditor(Editor):
    operations = [
        MultiplyOperation,
        DivideOperation,
        AddOperation,
        SetValueOperation,
    ]
    data_type = Decimal


class UnicodeEditor(Editor):
    operations = [
        ReplaceOperation,
        SetValueOperation,
    ]
    data_type = unicode


class ObjectEditor(Editor):
    operations = [
        SetObjectValueOperation,
    ]
    data_type = object


#
#   Fields
#

class Field(object):
    """Base class for fields in a mass editor

    This class implements basic value caching/storage for the editor
    """

    def __init__(self, data_type):
        self.data_type = data_type
        self.new_values = {}

    def get_value(self, item):  # pragma nocover
        raise NotImplementedError()

    def save_value(self, item):  # pragma nocover
        raise NotImplementedError()

    def get_column(self, spec):
        return Column('id', title=self.label, data_type=self.data_type,
                      format_func=self.format_func, format_func_data=self)

    def format_func(self, item, data=None):
        value = self.get_new_value(item)
        conv = converter.get_converter(self.data_type)
        if value is not None:
            return conv.as_string(value)
        return ''

    def set_new_value(self, item, value):
        old_value = self.get_value(item)
        if value == old_value:
            return
        self.new_values[item] = value

    def get_new_value(self, item):
        return self.new_values.get(item, self.get_value(item))

    def is_changed(self, item):
        return item in self.new_values


class AccessorField(Field):

    def __init__(self, label, obj_name, attribute, data_type, unique=False):
        """A field that updates a value of another object

        :param obj_name: the name of the object that will be updated, or None if
          the attribute will be accessed directly
        :param attribute: the attribute of obj that will be updated.
        :param unique: If the field is unique, the user will not be able to set
          the field to an specific value. FIXME: not implemented yet
        """
        super(AccessorField, self).__init__(data_type)
        self.label = label
        self.obj_name = obj_name
        self.attribute = attribute
        # FIXME: Use this
        self.unique = unique

    def _get_obj(self, item):
        if self.obj_name:
            return getattr(item, self.obj_name)
        return item

    def get_search_spec(self, spec):
        """Get the spec for filtering by this field."""
        obj = self._get_obj(spec)
        return getattr(obj, self.attribute)

    def get_value(self, item):
        obj = self._get_obj(item)
        return getattr(obj, self.attribute)

    def save_value(self, item):
        value = self.new_values[item]
        dest_obj = self._get_obj(item)
        setattr(dest_obj, self.attribute, value)

    def get_column(self, spec):
        # SearchColumn expects str instead of unicode and objects are rendered
        # as strings
        data_type = {unicode: str, object: str}.get(self.data_type, self.data_type)
        return SearchColumn('id', title=self.label, data_type=data_type,
                            format_func=self.format_func,
                            search_attribute=self.get_search_spec(spec),
                            format_func_data=self)


class ReferenceField(AccessorField):
    def __init__(self, label, obj_name, attribute, reference_class,
                 reference_attr):
        """A field that updates a reference to another object

        :param label: The label to be displayed
        :param obj_name: the name of the object that will be updated, or None if
          the attribute will be accessed directly
        :param attribute: the attribute of obj that will be updated.
        :param reference_class: the type of the reference that will be updated.
          This should be an Domain object
        :param reference_attr: The attribute of the referenced class that will
          be used for both rendering the column and filtering the results.
        """
        self._reference_class = reference_class
        self._reference_attr = reference_attr
        super(ReferenceField, self).__init__(label, obj_name, attribute,
                                             data_type=object, unique=False)

    def get_search_spec(self, spec=None):
        return getattr(self._reference_class, self._reference_attr)

    def format_func(self, item, data=None):
        value = self.get_new_value(item)
        if value is not None:
            return getattr(value, self._reference_attr)
        return ''


class MassEditorWidget(gtk.HBox):
    _editors = {
        currency: DecimalEditor,
        Decimal: DecimalEditor,
        unicode: UnicodeEditor,
        object: ObjectEditor,
    }

    def __init__(self, store, fields, results):
        self._store = store
        self._editor = None
        self._fields = fields
        self._results = results
        gtk.HBox.__init__(self, spacing=6)
        self._setup_widgets()

    def _filter_fields(self, data_type):
        return [f for f in self._fields if f.data_type == data_type]

    def _setup_editor(self, field):
        # Reuse editor if its possible
        if self._editor and self._editor.data_type == field.data_type:
            self._editor.set_field(field)
            return

        if self._editor:
            self.editor_placeholder.remove(self._editor)

        other_fields = self._filter_fields(field.data_type)
        klass = self._editors[field.data_type]
        self._editor = klass(self._store, field, other_fields)
        self.editor_placeholder.add(self._editor)

    def _setup_widgets(self):
        self.pack_start(gtk.Label(_('Update')), False, False)
        self.field_combo = ProxyComboBox()
        self.field_combo.connect('changed', self._on_field_combo__changed)
        self.pack_start(self.field_combo, False, False)
        self.editor_placeholder = gtk.EventBox()
        self.pack_start(self.editor_placeholder, False, False)
        self.apply_button = gtk.Button(stock=gtk.STOCK_APPLY)
        self.apply_button.connect('clicked', self._on_apply_button__clicked)
        self.pack_start(self.apply_button, False, False)

        for field in self._fields:
            self.field_combo.append_item(field.label, field)
        self.field_combo.select(self._fields[0])

    def _apply(self):
        marker('Updating values')
        for i in self._results:
            self._editor.apply_operation(i)
            self._results.refresh(i)
        marker('Done updating values')

    #
    # BaseEditorSlave
    #

    def confirm(self, dialog):
        marker('Saving data')
        for i, field in enumerate(self._fields):
            total = len(field.new_values)
            for i, item in enumerate(field.new_values):
                field.save_value(item)
                yield i, total

        marker('Done saving data')

    #
    #   Callbacks
    #

    def _on_field_combo__changed(self, combo):
        self._setup_editor(combo.get_selected())

    def _on_apply_button__clicked(self, button):
        self._apply()


class MassEditorSearch(SearchDialog):
    size = (850, 450)
    unlimited_results = True

    #: The fields that will be in the editor. If the editor needs more control
    #: wether the field should appear or not, get_fields can be used.
    default_fields = []

    def __init__(self, store):
        self._fields = self.get_fields(store)
        SearchDialog.__init__(self, store, hide_footer=False)
        self.set_ok_label(_('Save'))
        self.ok_button.set_sensitive(True)
        self.mass_editor = MassEditorWidget(store, self._fields, self.results)
        self.search.vbox.pack_start(self.mass_editor, False, False)
        self.search.vbox.reorder_child(self.mass_editor, 1)
        self.mass_editor.show_all()

    #
    # Public API
    #

    def get_fields(self, store):
        """Returns a list of fields for this mass editor

        Subclasses can override this if they want dynamic fields (that depend on
        a database state, for isntance)
        """
        return self.default_fields

    def get_items(self, store):  # pragma nocover
        """Get the list of objects that will be edited.

        Subclasses must override this
        """
        raise NotImplementedError()

    #
    #   SearchDialog implementation
    #

    def create_filters(self):
        self.search.set_query(self.get_items)
        self.search.result_view.set_cell_data_func(self._on_cell_data_func)

    def get_columns(self):
        marker('_get_columns')
        columns = []
        text_columns = []
        for field in self._fields:
            col = field.get_column(self.search_spec)
            columns.append(col)
            if field.data_type is unicode and isinstance(col, SearchColumn):
                text_columns.append(col.search_attribute)

        self.text_field_columns = text_columns
        marker('Done _get_columns')
        return columns

    def confirm(self, retval=None):
        # FIXME: Is there a nicer way to display this progress?
        self.ok_button.set_sensitive(False)
        self.cancel_button.set_sensitive(False)
        d = ProgressDialog(_('Updating items'), pulse=False)
        d.set_transient_for(self)
        d.start(wait=0)
        d.cancel.hide()

        for i, total in self.mass_editor.confirm(self):
            d.progressbar.set_text('%s/%s' % (i + 1, total))
            d.progressbar.set_fraction((i + 1) / float(total))
            while gtk.events_pending():
                gtk.main_iteration(False)

        d.stop()
        self.retval = True
        self.close()

    #
    #   Callbacks
    #

    def _on_cell_data_func(self, column, renderer, item, text):
        field = column.format_func_data
        is_changed = field.is_changed(item)
        renderer.set_property('weight-set', is_changed)
        if is_changed:
            text = field.format_func(item)
            renderer.set_property('weight', pango.WEIGHT_BOLD)
        return text
