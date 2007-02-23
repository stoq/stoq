# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s): Henrique Romano           <henrique@async.com.br>
##
""" System parameters editor"""

import gtk
from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.widgets.combo import ProxyComboEntry

from stoqlib.domain.base import AbstractModel
from stoqlib.domain.parameter import ParameterData
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.parameters import sysparam, get_parameter_details
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class SystemParameterEditor(BaseEditor):
    gladefile = "SystemParameterEditor"
    proxy_widgets = ("parameter_name",
                     "parameter_desc")
    model_type = ParameterData

    def __init__(self, conn, model):
        if not model:
            raise ValueError("This editor can't be called without a model")
        self._parameter_details = get_parameter_details(model.field_name)
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    #
    # Helper methods
    #

    def _setup_widgets(self):
        self.parameter_name.set_underline(True)
        self.parameter_desc.set_size("small")

    def _setup_entry_slave(self, justify_type=gtk.JUSTIFY_LEFT):
        widget = ProxyEntry()
        widget.data_type = unicode
        widget.model_attribute = "field_value"
        self.proxy.add_widget("field_value", widget)
        self.container.add(widget)
        widget.show()

    def _setup_comboboxentry_slave(self):
        widget = ProxyComboEntry()
        widget.model_attribute = "field_value"
        widget.data_type = unicode
        table = type(getattr(sysparam(self.conn), self.model.field_name))
        result = table.select(connection=self.conn)
        data = [(res.get_description(), str(res.id)) for res in result]
        widget.prefill(data)
        self.proxy.add_widget("field_value", widget)
        self.container.add(widget)
        widget.show()

    def _on_yes_radio__toggled(self, widget):
        self.model.field_value = ["0", "1"][widget.get_active()]

    def _on_no_radio__toggled(self, widget):
        self.model.field_value = ["1", "0"][widget.get_active()]

    def _setup_radio_slave(self):
        box = gtk.HBox()
        yes_widget = gtk.RadioButton()
        yes_widget.set_label(_("Yes"))
        yes_widget.connect("toggled", self._on_yes_radio__toggled)
        group = yes_widget.get_group()[0]
        box.pack_start(yes_widget)
        yes_widget.show()
        no_widget = gtk.RadioButton()
        no_widget.set_label(_("No"))
        no_widget.set_group(group)
        no_widget.connect("toggled", self._on_no_radio__toggled)
        box.pack_start(no_widget)
        no_widget.show()
        self.container.add(box)
        no_widget.set_active(self.model.field_value == "0")
        yes_widget.set_active(self.model.field_value == "1")
        box.show()

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
        data = getattr(sysparam(self.conn), self.model.field_name)
        if isinstance(data, AbstractModel):
            self._setup_comboboxentry_slave()
        elif isinstance(data, bool):
            self._setup_radio_slave()
        elif isinstance(data, (int, float)):
            self._setup_entry_slave()
        elif isinstance(data, unicode):
            self._setup_entry_slave()
        else:
            raise TypeError("ParameterData for `%s' has an invalid "
                            "type: %r" % (self.model.field_name, data))
