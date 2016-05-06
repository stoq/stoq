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

from kiwi.datatypes import ValidationError
from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.widgets.spinbutton import ProxySpinButton
from kiwi.ui.widgets.textview import ProxyTextView
from kiwi.ui.widgets.combo import ProxyComboEntry, ProxyComboBox

from stoqlib.domain.base import Domain
from stoqlib.domain.image import Image
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.parameter import ParameterData
from stoqlib.gui.slaves.imageslaveslave import ImageSlave
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SystemParameterEditor(BaseEditor):
    gladefile = "SystemParameterEditor"
    proxy_widgets = ("parameter_name",
                     "parameter_desc",
                     "parameter_group")
    model_type = ParameterData
    help_section = 'param'

    def __init__(self, store, param_detail):
        if not param_detail:
            raise ValueError("This editor can't be called without a model")
        # By default, if the user sets a value to None (e.g. selecting nothing
        # on a comboentry) we block it's update. Change this to False if the
        # param itself can accept None.
        self._block_none_value = True
        self.sensitive = True
        # TODO: After we migrate those parameters to set is_editable
        # to False we can probably remove this if
        if param_detail.key in ['DEMO_MODE', 'LOCAL_BRANCH',
                                'SYNCHRONIZED_MODE', 'USER_HASH']:
            self.sensitive = False

        self.detail = param_detail
        model = self._get_model(store, param_detail)
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    #
    # Helper methods
    #

    def _get_model(self, store, detail):
        model = store.find(ParameterData, field_name=detail.key).one()
        if not model:
            value = sysparam.get(detail.key)
            if detail.type is bool:
                value = int(value)
            if value is not None:
                value = unicode(value)
            model = ParameterData(store=store,
                                  field_name=detail.key,
                                  field_value=value)
        return model

    def _setup_widgets(self):
        self.parameter_name.set_underline(True)
        self.parameter_desc.set_size("small")
        self.parameter_group.set_label(self.detail.group)

    def _setup_entry_slave(self, box=None):
        widget = ProxyEntry()
        # Try to simulate insensitive appearance for non-editable entries
        # while keeping them selectable
        widget.set_editable(self.sensitive)
        if not self.sensitive:
            style = widget.get_style()
            widget.modify_text(
                gtk.STATE_NORMAL, style.text[gtk.STATE_INSENSITIVE])
            widget.modify_base(
                gtk.STATE_NORMAL, style.base[gtk.STATE_INSENSITIVE])
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
        data_type = self.detail.get_parameter_type()
        widget = ProxySpinButton(data_type=data_type)
        widget.props.sensitive = self.sensitive
        widget.set_range(self.detail.range[0], self.detail.range[1])
        widget.set_value(data_type(self.model.field_value))
        widget.set_increments(1, 10)
        if issubclass(data_type, Decimal):
            widget.props.digits = 2

        widget.connect('value-changed', self._on_spin__value_changed)
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
        if self.detail.wrap:
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

    def _setup_image_slave(self):
        event_box = gtk.EventBox()
        event_box.show()

        field_name = self.model.field_name
        model = sysparam.get_object(self.store, field_name)

        self.container.add(event_box)
        self._image_slave = ImageSlave(self.store, model)
        self._image_slave.connect('image-changed',
                                  self._on_image_slave__image_changed)
        self._image_slave.show()
        self.attach_slave('image_slave', self._image_slave, event_box)

        # Images can have field_value as None
        self._block_none_value = False

    def _setup_comboboxentry_slave(self, data=None):
        widget = ProxyComboEntry()
        widget.props.sensitive = self.sensitive
        widget.model_attribute = "field_value"
        widget.data_type = unicode

        detail = sysparam.get_detail_by_name(self.model.field_name)
        is_mandatory = not detail.allow_none
        self._block_none_value = is_mandatory
        widget.set_property('mandatory', is_mandatory)

        if not data:
            field_type = detail.get_parameter_type()
            # FIXME: DEFAULT_PAYMENT_METHOD needs to filter information from
            # domain because it cannot be any non-creatable method.
            # Find a way to implement this in a generic on ParameterDetails
            if self.model.field_name == "DEFAULT_PAYMENT_METHOD":
                result = PaymentMethod.get_creatable_methods(
                    self.store, Payment.TYPE_IN, False)
            else:
                result = self.store.find(field_type)
            data = [(res.get_description(), unicode(res.id)) for res in result]
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

        data = [(value, unicode(key))
                for key, value in self.detail.options.items()]
        widget.prefill(data)
        self.proxy.add_widget("field_value", widget)
        self.container.add(widget)
        widget.show()

    #
    # BaseEditor hooks
    #

    def get_title(self, model):
        return _("Edit '%s' Parameter") % self.detail.short_desc

    def setup_proxies(self):
        self.add_proxy(self.detail,
                       SystemParameterEditor.proxy_widgets)
        self.proxy = self.add_proxy(self.model)

    def setup_slaves(self):
        field_type = self.detail.get_parameter_type()
        if issubclass(field_type, Image):
            self._setup_image_slave()
        elif issubclass(field_type, Domain):
            self._setup_comboboxentry_slave()
        elif self.detail.editor == 'file-chooser':
            self._setup_entry_with_filechooser_button_slave()
        elif self.detail.editor == 'directory-chooser':
            self._setup_entry_with_filechooser_button_slave(dir_only=True)
        elif issubclass(field_type, bool):
            self._setup_radio_slave()
        elif issubclass(field_type, (int, float, Decimal)):
            if self.detail.options:
                self._setup_options_combo_slave()
            elif self.detail.range:
                self._setup_spin_entry_slave()
            else:
                self._setup_entry_slave()
        elif issubclass(field_type, basestring):
            if self.detail.multiline:
                self._setup_text_view_slave()
            elif self.detail.combo_data:
                self._setup_comboboxentry_slave(data=self.detail.combo_data())
            else:
                self._setup_entry_slave()
        else:
            raise TypeError("ParameterData for `%s' has an invalid "
                            "type: %r" % (self.model.field_name,
                                          field_type))

    def validate_confirm(self):
        if self._block_none_value and self.model.field_value is None:
            return False

        change_callback = self.detail.get_change_callback()
        if change_callback:
            change_callback(self.model.field_value, self.store)

        sysparam.set_value_generic(self.model.field_name,
                                   self.model.field_value)

        return True

    #
    # Callbacks
    #

    def _on_image_slave__image_changed(self, slave, image):
        self.model.field_value = image and unicode(image.id)

    def _on_entry__validate(self, widget, value):
        if not value:
            return ValidationError(_("Field can not be empty."))

        validate_func = self.detail.get_parameter_validator()
        if validate_func and callable(validate_func):
            return validate_func(value)

    def _on_entry__validation_changed(self, widget, value):
        # FIXME: 1- The BaseModel (or one of it's parent classes) should be
        #           doing the next logic automatically.
        #        2- Why does refresh_ok only accepts int values?
        #           If a bool value is passed, it'll raise TypeError.
        self.refresh_ok(int(value))

    def _on_yes_radio__toggled(self, widget):
        self.model.field_value = unicode(int(widget.get_active()))

    def _on_spin__value_changed(self, widget):
        data_type = self.detail.get_parameter_type()
        if data_type is int:
            # float and Decimal are subclasses of int
            value = widget.get_value_as_int()
        else:
            value = widget.read()

        self.model.field_value = unicode(value)

    def _on_filechooser_button__selection_changed(self, widget):
        filename = widget.get_filename()
        self._entry.set_text(filename)
