# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2008 Async Open Source <http://www.async.com.br>
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
""" System parameters editor"""

from decimal import Decimal
import gtk

from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.widgets.spinbutton import ProxySpinButton
from kiwi.ui.widgets.textview import ProxyTextView
from kiwi.ui.widgets.combo import ProxyComboEntry, ProxyComboBox

from stoqlib.domain.base import AbstractModel
from stoqlib.domain.parameter import ParameterData
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.imageutils import ImageHelper
from stoqlib.lib.parameters import (sysparam, get_parameter_details,
                                    DirectoryParameter)
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SystemParameterEditor(BaseEditor):
    gladefile = "SystemParameterEditor"
    proxy_widgets = ("parameter_name",
                     "parameter_desc")
    model_type = ParameterData
    help_section = 'param'

    def __init__(self, conn, model):
        if not model:
            raise ValueError("This editor can't be called without a model")
        self.sensitive = True
        if model.field_name in ['DEMO_MODE']:
            self.sensitive = False

        self._parameter_details = get_parameter_details(model.field_name)
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()
    #
    # Helper methods
    #

    def _setup_widgets(self):
        self.parameter_name.set_underline(True)
        self.parameter_desc.set_size("small")

    def _setup_entry_slave(self, box=None):
        widget = ProxyEntry()
        widget.props.sensitive = self.sensitive
        widget.data_type = unicode
        widget.model_attribute = "field_value"
        self.proxy.add_widget("field_value", widget)
        if box is None:
            self.container.add(widget)
        else:
            box.pack_start(widget)

        widget.show()
        widget.connect('validate', self._on_entry__validate)
        widget.connect('validation-changed',
                       self._on_entry__validation_changed)

        self._entry = widget

    def _setup_spin_entry_slave(self, box=None):
        widget = ProxySpinButton()
        widget.props.sensitive = self.sensitive
        widget.data_type = int
        widget.set_range(self.constant.range[0], self.constant.range[1])
        widget.set_value(int(self.model.field_value))
        widget.set_increments(1, 10)
        widget.connect('changed', self._on_spin_changed)
        if box is None:
            self.container.add(widget)
        else:
            box.pack_start(widget)

        widget.show()
        widget.connect('validate', self._on_entry__validate)
        widget.connect('validation-changed',
                       self._on_entry__validation_changed)
        self._entry = widget

    def _setup_text_view_slave(self):
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC,
                      gtk.POLICY_AUTOMATIC)
        widget = ProxyTextView()
        widget.props.sensitive = self.sensitive
        widget.data_type = unicode
        widget.model_attribute = "field_value"
        widget.set_wrap_mode(gtk.WRAP_WORD)
        self.proxy.add_widget("field_value", widget)
        sw.add(widget)
        sw.show()
        self.container.add(sw)

        widget.show()
        self._entry = widget

    def _setup_entry_with_filechooser_button_slave(self, dir_only=False):
        hbox = gtk.HBox(spacing=6)
        hbox.props.sensitive = self.sensitive
        self._setup_entry_slave(hbox)
        title = _(u'Cat 52 directory selection')
        filechooser_button = gtk.FileChooserButton(title)
        filechooser_button.connect('selection-changed',
            self._on_filechooser_button__selection_changed)

        if dir_only:
            filechooser_button.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

        hbox.pack_start(filechooser_button, expand=False)
        filechooser_button.show()

        self.container.add(hbox)
        hbox.show()

    def _setup_comboboxentry_slave(self):
        widget = ProxyComboEntry()
        widget.props.sensitive = self.sensitive
        widget.model_attribute = "field_value"
        widget.data_type = unicode
        widget.mandatory = True
        field_type = sysparam(self.conn).get_parameter_type(self.model.field_name)
        result = field_type.select(connection=self.conn)
        data = [(res.get_description(), str(res.id)) for res in result]
        widget.prefill(data)
        self.proxy.add_widget("field_value", widget)
        self.container.add(widget)
        widget.show()
        widget.connect('validation-changed',
                       self._on_entry__validation_changed)

    def _setup_radio_slave(self):
        box = gtk.HBox()
        box.props.sensitive = self.sensitive
        yes_widget = gtk.RadioButton()
        yes_widget.set_label(_("Yes"))
        yes_widget.connect("toggled", self._on_yes_radio__toggled)
        group = yes_widget.get_group()[0]
        box.pack_start(yes_widget)
        yes_widget.show()
        no_widget = gtk.RadioButton()
        no_widget.set_label(_("No"))
        no_widget.set_group(group)
        box.pack_start(no_widget)
        no_widget.show()
        self.container.add(box)
        no_widget.set_active(self.model.field_value == "0")
        yes_widget.set_active(self.model.field_value == "1")
        box.show()

    def _setup_options_combo_slave(self):
        widget = ProxyComboBox()
        widget.props.sensitive = self.sensitive
        widget.model_attribute = "field_value"
        widget.data_type = unicode

        data = [(value, str(key))
                for key, value in self.constant.options.items()]
        widget.prefill(data)
        self.proxy.add_widget("field_value", widget)
        self.container.add(widget)
        widget.show()

    #
    # BaseEditor hooks
    #

    def get_title(self, model):
        return _("Edit '%s' Parameter") % self._parameter_details.short_desc

    def setup_proxies(self):
        self.add_proxy(self._parameter_details,
                       SystemParameterEditor.proxy_widgets)
        self.proxy = self.add_proxy(self.model)

    def setup_slaves(self):
        self._slave = None
        sparam = sysparam(self.conn)
        self.constant = sparam.get_parameter_constant(self.model.field_name)
        field_type = self.constant.get_parameter_type()
        if issubclass(field_type, AbstractModel):
            self._setup_comboboxentry_slave()
        elif issubclass(field_type, ImageHelper):
            self._setup_entry_with_filechooser_button_slave()
        elif issubclass(field_type, DirectoryParameter):
            self._setup_entry_with_filechooser_button_slave(dir_only=True)
        elif issubclass(field_type, bool):
            self._setup_radio_slave()
        elif issubclass(field_type, (int, float)):
            if self.constant.options:
                self._setup_options_combo_slave()
            elif self.constant.range:
                self._setup_spin_entry_slave()
            else:
                self._setup_entry_slave()
        elif issubclass(field_type, basestring):
            if self.constant.multiline:
                self._setup_text_view_slave()
            else:
                self._setup_entry_slave()
        elif issubclass(field_type, Decimal):
            self._setup_entry_slave()
        else:
            raise TypeError("ParameterData for `%s' has an invalid "
                            "type: %r" % (self.model.field_name,
                                          field_type))

    def on_confirm(self):
        if self.model.field_value is None:
            return False
        return self.model

    #
    # Callbacks
    #

    def _on_entry__validate(self, widget, value):
        validate_func = self.constant.get_parameter_validator()
        if validate_func and callable(validate_func):
            return validate_func(value)

    def _on_entry__validation_changed(self, widget, value):
        # FIXME: 1- The BaseModel (or one of it's parent classes) should be
        #           doing the next logic automatically.
        #        2- Why does refresh_ok only accepts int values?
        #           If a bool value is passed, it'll raise TypeError.
        self.refresh_ok(int(value))

    def _on_yes_radio__toggled(self, widget):
        self.model.field_value = str(int(widget.get_active()))

    def _on_spin_changed(self, widget):
        self.model.field_value = str(widget.get_value_as_int())

    def _on_filechooser_button__selection_changed(self, widget):
        filename = widget.get_filename()
        self._entry.set_text(filename)
