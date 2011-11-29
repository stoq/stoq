
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
##
""" Editors implementation for Stoq devices configuration"""

from stoqdrivers.interfaces import IChequePrinter
from stoqdrivers.printers.base import (get_supported_printers,
                                       get_supported_printers_by_iface)
from stoqdrivers.scales.base import get_supported_scales

from stoqlib.api import api
from stoqlib.domain.devices import DeviceSettings
from stoqlib.domain.person import BranchStation
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.devicemanager import DeviceManager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class DeviceSettingsEditor(BaseEditor):
    gladefile = 'DeviceSettingsEditor'
    model_type = DeviceSettings
    proxy_widgets = ('type_combo',
                     'brand_combo',
                     'device_combo',
                     'model_combo',
                     'station',
                     'is_active_button')

    def __init__(self, conn, model=None, station=None):
        if station is not None and not isinstance(station, BranchStation):
            raise TypeError("station should be a BranchStation")
        self._device_manager = DeviceManager()
        self.printers_dict = get_supported_printers()
        self._branch_station = station
        # This attribute is set to True when setup_proxies is finished
        self._is_initialized = False
        BaseEditor.__init__(self, conn, model)
        self._original_brand = self.model.brand
        self._original_model = self.model.model

    def refresh_ok(self, *args):
        if self._is_initialized:
            BaseEditor.refresh_ok(self, self.model.is_valid())

    def setup_station_combo(self):
        if self._branch_station:
            self.station.prefill([(self._branch_station.name,
                                   self._branch_station)])
            self.model.station = self._branch_station
            self.station.set_sensitive(False)
            return
        self.station.prefill(
            [(station.name, station)
                 for station in BranchStation.select(connection=self.conn)])

    def setup_device_port_combo(self):
        items = [(_("Choose..."), None)]
        items.extend([(device.device_name, device.device_name) for device
                      in self._device_manager.get_serial_devices()])
        self.device_combo.prefill(items)

    def setup_device_types_combo(self):
        items = [(_("Choose..."), None)]
        device_types = (# TODO: Reenable when we have cheque printers working.
                        #DeviceSettings.CHEQUE_PRINTER_DEVICE,
                        DeviceSettings.SCALE_DEVICE, )
        items.extend([(self.model.get_device_type_name(t), t)
                      for t in device_types])
        self.type_combo.prefill(items)

    def setup_widgets(self):
        self.setup_device_types_combo()
        self.setup_device_port_combo()
        self.setup_station_combo()
        if not self.edit_mode:
            self.is_active_button.set_sensitive(False)

    def _get_supported_types(self):
        if self.model.type == DeviceSettings.SCALE_DEVICE:
            supported_types = get_supported_scales()
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
        self._is_initialized = True

    def create_model(self, conn):
        return DeviceSettings(device_name=None,
                              station=api.get_current_station(conn),
                              brand=None,
                              model=None,
                              type=None,
                              connection=conn)

    def get_title(self, *args):
        if self.edit_mode:
            return _("Edit Device for %s") % self.model.station.name
        else:
            return _("Add Device")

    def validate_confirm(self):
        if not self.edit_mode:
            settings = DeviceSettings.get_by_station_and_type(
                conn=api.get_connection(),
                station=self.model.station.id,
                type=self.model.type)
            if settings:
                self.station.set_invalid(
                    _(u"A %s already exists for station \"%s\"")
                      % (self.model.get_device_type_name(),
                         self.model.station.name))
                return False
        return True

    #
    # Kiwi callbacks
    #

    def on_brand_combo__changed(self, *args):
        self.update_model_combo()
        self.refresh_ok()

    def on_type_combo__changed(self, *args):
        self.update_brand_combo()
        self.refresh_ok()

    def on_brand_combo__state_changed(self, *args):
        self.update_model_combo()
        self.refresh_ok()

    def on_model_combo__changed(self, *args):
        self.refresh_ok()

    def on_device_combo__changed(self, *args):
        self.refresh_ok()
