# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Author(s): Henrique Romano <henrique@async.com.br>
##
##
""" Editors implementation for Stoq devices configuration"""

import re
import string
from socket import gethostname

from kiwi.ui.objectlist import Column
from kiwi.python import Settable
from kiwi.decorators import signal_block
from sqlobject.sqlbuilder import AND
from stoqdrivers.devices.printers.base import (get_supported_printers,
                                               get_supported_printers_by_iface)
from stoqdrivers.devices.scales.base import get_supported_scales
from stoqdrivers.devices.printers.interface import (ICouponPrinter,
                                                    IChequePrinter)
from stoqdrivers.constants import describe_constant

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import warning
from stoqlib.lib.runtime import get_connection
from stoqlib.lib.defaults import (get_method_names, METHOD_MONEY, METHOD_CHECK,
                                  METHOD_MULTIPLE, UNKNOWN_CHARACTER)
from stoqlib.domain.devices import DeviceSettings, DeviceConstants
from stoqlib.gui.base.editors import BaseEditor
from stoqlib.gui.base.lists import AdditionListDialog
from stoqlib.gui.base.dialogs import run_dialog

_ = stoqlib_gettext

class DeviceConstantsEditor(BaseEditor):
    gladefile = "DeviceConstantsEditor"
    # I'm requesting DeviceSettings as model here because I want to be able
    # to set the editor's title without *hacks*. No processing is done with
    # this object apart the one in get_title method.
    model_type = DeviceSettings
    size = (500, 400)
    proxy_widgets = ("ascii_value",
                     "description")

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)

    def _format_value(self, value):
        return value is not None and value or _("Not Defined")

    def _get_columns(self):
        return [Column("description", title=_(u"Description"),
                       data_type=unicode, expand=True),
                Column("value", title=_(u"Value"), data_type=str, width=100,
                       format_func=self._format_value)]

    def _setup_widgets(self):
        self.klist.set_columns(self._get_columns())
        data = [Settable(identifier=item, stoq_specific=False,
                         description=describe_constant(item),
                         value=self._constants.get_value(item))
                        for item in self._constants.get_items()]
        for ident, name in get_method_names().items():
            if ident in (METHOD_MONEY, METHOD_CHECK, METHOD_MULTIPLE):
                continue
            data.append(Settable(identifier=ident, stoq_specific=True,
                                 description=_(u"%s Payment Method") % name,
                                 value=self._pm_constants.get_value(ident)))
        self.klist.add_list(data)

    def _update_hex_value(self):
        self.hex_value.set_text(
            "".join([data.encode("hex")
                         for data in self.ascii_value.get_text()]))

    @signal_block('ascii_value.changed')
    def _update_ascii_value(self):
        text = ""
        hex_text = self.hex_value.get_text()
        for data in re.compile("[0-9a-fA-F]{1,2}").findall(hex_text):
            data = data.zfill(2).decode("hex")
            if not data in string.printable:
                text += UNKNOWN_CHARACTER
            else:
                text += data
        self.ascii_value.set_text(text)

    #
    # BaseEditor hooks
    #

    def get_title(self, model):
        return _(u"Editing constants for %s") % model.get_printer_description()

    def setup_proxies(self):
        if (self.model is None or self.model.constants is None
            or self.model.pm_constants is None):
            raise ValueError("A valid model is required by this editor (%r)"
                             % self)
        self._pm_constants = self.model.pm_constants
        self._constants = self.model.constants
        self._setup_widgets()
        self._proxy = self.add_proxy(None, DeviceConstantsEditor.proxy_widgets)

    def on_confirm(self):
        # I just can't modify a dictionary's item value, because in this way
        # the change will not be persisted -- so I need to create a new dict
        # and associate this to the PickleCol directly.
        data = {}
        stoq_data = {}
        for item in self.klist:
            if item.stoq_specific:
                stoq_data[item.identifier] = item.value
            else:
                data[item.identifier] = item.value
        self.model.constants.set_constants(data)
        self.model.pm_constants.set_constants(stoq_data)
        return self.model

    #
    # Kiwi callbacks
    #

    def on_klist__selection_changed(self, widget, item):
        self._proxy.set_model(item)
        self._update_hex_value()

    def on_ascii_value__changed(self, *args):
        self._update_hex_value()
        self.klist.update(self._proxy.model)

    def on_hex_value__changed(self, *args):
        self._update_ascii_value()
        self.klist.update(self._proxy.model)

class DeviceSettingsEditor(BaseEditor):
    gladefile = 'DeviceSettingsEditor'
    model_type = DeviceSettings
    proxy_widgets = ('type_combo',
                     'brand_combo',
                     'device_combo',
                     'model_combo',
                     'host',
                     'is_active_button')

    def __init__(self, conn, model=None):
        self.printers_dict = get_supported_printers()
        BaseEditor.__init__(self, conn, model)
        self._original_brand = self.model.brand
        self._original_model = self.model.model

    def setup_device_port_combo(self):
        device_types = (DeviceSettings.DEVICE_SERIAL1,
                        DeviceSettings.DEVICE_SERIAL2,
                        DeviceSettings.DEVICE_PARALLEL)
        items = [(self.model.get_device_description(device), device)
                     for device in device_types]
        self.device_combo.prefill(items)

    def setup_device_types_combo(self):
        items = [(_("Choose..."), None)]
        device_types = (DeviceSettings.SCALE_DEVICE,
                        DeviceSettings.FISCAL_PRINTER_DEVICE,
                        DeviceSettings.CHEQUE_PRINTER_DEVICE)
        items.extend([(self.model.get_device_type_name(t), t)
                      for t in device_types])
        self.type_combo.prefill(items)

    def setup_widgets(self):
        self.setup_device_types_combo()
        self.setup_device_port_combo()

    def _get_supported_types(self):
        if self.model.type == DeviceSettings.SCALE_DEVICE:
            supported_types = get_supported_scales()
        elif self.model.type == DeviceSettings.FISCAL_PRINTER_DEVICE:
            supported_types = get_supported_printers_by_iface(ICouponPrinter)
        elif self.model.type == DeviceSettings.CHEQUE_PRINTER_DEVICE:
            supported_types = get_supported_printers_by_iface(IChequePrinter)
        else:
            raise TypeError("The selected device type isn't supported")
        return supported_types

    def _get_supported_brands(self):
        return self._get_supported_types().keys()

    def _get_supported_models(self):
        return self._get_supported_types()[self.model.brand]

    def update_brand_combo(self):
        self.brand_combo.clear()
        self.brand_combo.set_sensitive(self.model.type is not None)
        if self.model.type is None:
            return
        items = [(_("Choose..."), None)]
        brand_list = self._get_supported_brands()
        supported_brands = self._get_supported_brands()
        items.extend([(brand.capitalize(), brand)
                          for brand in supported_brands])
        self.brand_combo.prefill(items)

    def update_model_combo(self):
        self.model_combo.clear()
        brand = self.model.brand
        self.model_combo.set_sensitive(brand is not None)
        if self.model.brand is None:
            return
        supported_models = self._get_supported_models()
        items = [(_("Choose..."), None)]
        items.extend([(obj.model_name, obj.__name__)
                          for obj in supported_models])
        self.model_combo.prefill(items)

    def _update_constants_button(self, *args):
        self.constants_button.set_sensitive(bool(self.model.device
                                                 and self.model.model
                                                 and self.model.brand))

    def _edit_driver_constants(self, *args):
        if ((self._original_brand != self.model.brand
             or self._original_model != self.model.model)
            or self.model.constants is None):
            driver = self.model.get_interface()
            constants = driver.get_constants()
            new_consts = dict([(item, constants.get_value(item))
                                   for item in constants.get_items()])
            if not self.model.constants:
                self.model.constants = DeviceConstants(constants=new_consts,
                                                       connection=self.conn)
            else:
                self.model.constants.set_constants(new_consts)
        run_dialog(DeviceConstantsEditor, self, self.conn, self.model)

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self.setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    DeviceSettingsEditor.proxy_widgets)

    def create_model(self, conn):
        return DeviceSettings(host=gethostname(),
                              device=DeviceSettings.DEVICE_SERIAL1,
                              brand=None,
                              model=None,
                              type=None,
                              connection=conn)

    def get_title(self, *args):
        if self.edit_mode:
            return _("Edit Device for %s" % self.model.host)
        else:
            return _("Add Device")

    def _get_existing_printer_basequery(self):
        q1 = DeviceSettings.q.host == self.model.host
        q2 = DeviceSettings.q.type == self.model.type
        return AND(q1, q2)


    def validate_confirm(self):
        if not self.edit_mode:
            conn = get_connection()
            basequery = self._get_existing_printer_basequery()
            q2 = DeviceSettings.q.brand != 'virtual'
            query = AND(basequery, q2)
            settings = DeviceSettings.select(query, connection=conn)
            if settings.count():
                self.host.set_invalid(_("A device of type %s already exists "
                                        "for host %s")
                                      % (self.model.get_device_type_name(),
                                         self.model.host))
                return False
        return True

    # FIXME: this part will improved when bug #2334 is fixed.
    def on_confirm(self):
        conn = get_connection()
        if not self.edit_mode and (not self.model.constants
                                   or not self.model.pm_constants):
            warning( _(u"The printer will be disabled"),
                     _(u"The printer will be disabled automatically "
                        "because there are no constants defined yet."))
            self.model.inactivate()
        basequery = self._get_existing_printer_basequery()
        q2 = DeviceSettings.q.brand == 'virtual'
        query = AND(basequery, q2)
        settings = DeviceSettings.select(query, connection=conn)
        if settings.count():
            DeviceSettings.delete(settings[0].id, connection=self.conn)
        self.conn.commit()
        return self.model

    #
    # Kiwi callbacks
    #

    def on_brand_combo__changed(self, *args):
        self.update_model_combo()
        self._update_constants_button()

    def on_type_combo__changed(self, *args):
        self.update_brand_combo()
        self._update_constants_button()

    def on_brand_combo__state_changed(self, *args):
        self.update_model_combo()
        self._update_constants_button()

    def on_model_combo__changed(self, *args):
        self._update_constants_button()

    def on_device_combo__changed(self, *args):
        self._update_constants_button()

    def on_constants_button__clicked(self, *args):
        self._edit_driver_constants()

class DeviceSettingsDialog(AdditionListDialog):
    size = (600, 500)
    def __init__(self, conn):
        AdditionListDialog.__init__(self, conn, DeviceSettingsEditor,
                                    self.get_columns(), self.get_items(conn),
                                    title=_("Devices"))
        self.set_before_delete_items(self.before_delete_items)

    #
    # Helper methods
    #

    def get_columns(self):
        return [Column('device_type_name', _('Device Type'), data_type=str,
                       sorted=True, width=120),
                Column('printer_description', _('Description'), data_type=str,
                       expand=True),
                Column('host', _('Host'), data_type=str, width=150,
                       searchable=True),
                Column('is_active', _("Active"), data_type=bool, width=100)]

    def get_items(self, conn):
        query = DeviceSettings.q.brand != 'virtual'
        return DeviceSettings.select(query, connection=conn)

    #
    # Callbacks
    #

    def before_delete_items(self, list_slave, items):
        table = DeviceSettings
        for item in items:
            table.delete(item.id, connection=self.conn)
        self.conn.commit()
