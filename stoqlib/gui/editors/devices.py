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

from kiwi.ui.widgets.list import Column
from sqlobject.sqlbuilder import AND
from stoqdrivers.devices.printers.base import (get_supported_printers,
                                               get_supported_printers_by_iface)
from stoqdrivers.devices.scales.base import get_supported_scales
from stoqdrivers.devices.printers.interface import (ICouponPrinter,
                                                    IChequePrinter)

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.runtime import get_connection
from stoqlib.domain.devices import DeviceSettings
from stoqlib.gui.base.editors import BaseEditor
from stoqlib.gui.base.lists import AdditionListDialog

_ = stoqlib_gettext


class DeviceSettingsEditor(BaseEditor):
    gladefile = 'DeviceSettingsEditor'
    model_type = DeviceSettings
    proxy_widgets = ('type_combo',
                     'brand_combo',
                     'device_combo',
                     'model_combo',
                     'host')

    def __init__(self, conn, model=None):
        self.printers_dict = get_supported_printers()
        BaseEditor.__init__(self, conn, model)

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

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self.setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    DeviceSettingsEditor.proxy_widgets)

    def create_model(self, conn):
        return DeviceSettings(host='', device=None, brand=None, model=None,
                              type=None, connection=conn)

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

    def on_type_combo__changed(self, *args):
        self.update_brand_combo()

    def on_brand_combo__state_changed(self, *args):
        self.update_model_combo()

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
                       searchable=True)]

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
