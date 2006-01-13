# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Henrique Romano <henrique@async.com.br>
##
"""
stoq/gui/editors/devices.py:

    Editors implementation for Stoq devices configuration.
"""

import gettext

import gtk
from kiwi.ui.widgets.list import Column
from stoqdrivers.devices.printers.base import get_supported_printers
from stoqdrivers.devices.scales.base import get_supported_scales
from stoqlib.gui.editors import BaseEditor
from stoqlib.gui.lists import AdditionListDialog
from stoqlib.gui.search import SearchEditor

from stoq.domain.devices import DeviceSettings

_ = gettext.gettext

class DeviceSettingsEditor(BaseEditor):
    gladefile = 'DeviceSettingsEditor'
    model_type = DeviceSettings
    widgets = ('type_combo',
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
                        DeviceSettings.PRINTER_DEVICE)
        items.extend([(self.model.get_device_type_name(t), t)
                      for t in device_types])
        self.type_combo.prefill(items)

    def setup_widgets(self):
        self.setup_device_types_combo()
        self.setup_device_port_combo()

    def _get_supported_types(self):
        if self.model.type == DeviceSettings.SCALE_DEVICE:
            supported_types = get_supported_scales()
        elif self.model.type == DeviceSettings.PRINTER_DEVICE:
            supported_types = get_supported_printers()
        else:
            raise TypeError("The selected device type "
                            "isn't supported")
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
        self.proxy = self.add_proxy(model=self.model, widgets=self.widgets)

    def create_model(self, conn):
        return DeviceSettings(host='', device=None, brand=None, model=None,
                              type=None, connection=conn)

    def get_title(self, *args):
        if self.edit_mode:
            return _("Edit Device for %s" % self.model.host)
        else:
            return _("Add Device")

    # FIXME: this part will improved when bug #2334 is fixed.
    def on_confirm(self):
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
        return DeviceSettings.select(connection=conn)

    #
    # Callbacks
    #

    def before_delete_items(self, list_slave, items):
        table = DeviceSettings
        for item in items:
            table.delete(item.id, connection=self.conn)
        self.conn.commit()

