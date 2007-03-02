# -*- coding: utf-8 -*-
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
## Author(s): Henrique Romano <henrique@async.com.br>
##            Johan Dahlin    <jdahlin@async.com.br>
##
##
""" Editors implementation for Stoq devices configuration"""

import re
import string

import gtk
from kiwi.decorators import signal_block
from kiwi.python import Settable
from kiwi.ui.objectlist import Column, ObjectList

from stoqdrivers.devices.interfaces import (ICouponPrinter,
                                            IChequePrinter)
from stoqdrivers.devices.printers.base import (get_supported_printers,
                                               get_supported_printers_by_iface)
from stoqdrivers.devices.scales.base import get_supported_scales

from stoqlib.database.runtime import get_connection, get_current_station
from stoqlib.domain.devices import DeviceSettings, DeviceConstant
from stoqlib.domain.person import BranchStation
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.base.dialogs import BasicDialog, run_dialog
from stoqlib.gui.base.lists import AdditionListSlave
from stoqlib.lib.defaults import UNKNOWN_CHARACTER
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

_HEX_REGEXP = re.compile("[0-9a-fA-F]{1,2}")

def dec2hex(dec):
    return "".join([data.encode("hex") for data in dec])

def hex2dec(hex):
    dec = ""
    for data in _HEX_REGEXP.findall(hex):
        data = data.zfill(2).decode("hex")
        if not data in string.printable:
            data = UNKNOWN_CHARACTER
        dec += data
    return dec

class DeviceConstantEditor(BaseEditor):
    gladefile = 'DeviceConstantEditor'
    model_type = DeviceConstant
    model_name = _('Device constant')
    proxy_widgets = ('constant_name',
                     'constant_value',
                     'constant_type_description',
                     'device_value',
                     'device_value_hex',
                     )

    def __init__(self, conn, model=None, settings=None, constant_type=None):
        if not isinstance(settings, DeviceSettings):
            raise TypeError("settings should be a DeviceSettings, not %s" % settings)
        self.settings = settings
        self.constant_type = constant_type

        BaseEditor.__init__(self, conn, model)

        # Hide value label/entry for non tax types
        if constant_type != DeviceConstant.TYPE_TAX:
            self.label_value.hide()
            self.constant_value.hide()

    @signal_block('device_value.content_changed')
    def _update_dec(self, value):
        self.device_value.set_text(value)

    @signal_block('device_value_hex.content_changed')
    def _update_hex(self, value):
        self.device_value_hex.set_text(value)


    #
    # BaseEditor
    #

    def create_model(self, conn):
        return DeviceConstant(device_settings=self.settings,
                              connection=conn,
                              constant_type=self.constant_type,
                              constant_value=None,
                              constant_name="Unnamed")

    def on_confirm(self):
        return self.model

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    DeviceConstantEditor.proxy_widgets)
        self.proxy.update('device_value')

    #
    # Callbacks
    #

    def on_device_value_hex__content_changed(self, entry):
        self._update_dec(hex2dec(entry.get_text()))

    def on_device_value__content_changed(self, entry):
        self._update_hex(dec2hex(entry.get_text()))

class DeviceConstantsList(AdditionListSlave):
    def __init__(self, conn, settings):
        self._settings = settings
        self._constant_type = None
        AdditionListSlave.__init__(self, conn,
                                   self._get_columns())
        self.connect('on-add-item', self._on_list_slave__add_item)
        self.connect('before-delete-items',
                     self._on_list_slave__before_delete_items)

    def _get_columns(self):
        return [Column('constant_name', _('Name'), expand=True),
                Column('device_value', _('Value'), data_type=str,
                       width=120, format_func=lambda x: repr(x)[1:-1])]

    def _before_delete_items(self, list_slave, items):
        for item in items:
            DeviceSettings.delete(item.id, connection=self.conn)
        self.conn.commit()
        self._refresh()

    def _refresh(self):
        self.klist.clear()
        self.klist.extend(self._settings.get_constants_by_type(
            self._constant_type))

    #
    # AdditionListSlave
    #

    def run_editor(self, model):
        return run_dialog(DeviceConstantEditor, conn=self.conn,
                          model=model,
                          settings=self._settings,
                          constant_type=self._constant_type)

    #
    # Public API
    #

    def switch(self, constant_type):
        self._constant_type = constant_type
        self._refresh()

    #
    # Callbacks
    #

    def _on_list_slave__add_item(self, slave, item):
        self._refresh()

    def _on_list_slave__before_delete_items(self, slave, items):
        for item in items:
            DeviceConstant.delete(item.id, connection=self.conn)


class DeviceConstantsDialog(BasicDialog):
    size = (500, 300)
    def __init__(self, conn, settings):
        self._constant_slave = None
        self.conn = conn
        self.settings = settings

        BasicDialog.__init__(self)
        BasicDialog._initialize(self, hide_footer=False, title='edit',
                                size=self.size)
        self.main.set_border_width(6)

        self._create_ui()

    def _create_ui(self):
        hbox = gtk.HBox()
        self.klist = ObjectList([Column('name')])
        self.klist.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
        self.klist.set_size_request(150, -1)
        self.klist.get_treeview().set_headers_visible(False)
        self.klist.connect('selection-changed',
                           self._on_klist__selection_changed)
        hbox.pack_start(self.klist)
        hbox.show()

        for name, ctype in [(_('Units'), DeviceConstant.TYPE_UNIT),
                            (_('Tax'), DeviceConstant.TYPE_TAX),
                            (_('Payments'), DeviceConstant.TYPE_PAYMENT)]:
            self.klist.append(Settable(name=name, type=ctype))
        self.klist.show()

        self._constant_slave = DeviceConstantsList(self.conn, self.settings)
        self._constant_slave.switch(DeviceConstant.TYPE_UNIT)

        hbox.pack_start(self._constant_slave.get_toplevel())

        # FIXME: redesign BasicDialog
        self.main.remove(self.main_label)
        self.main.add(hbox)

        hbox.show_all()


    #
    # Callbacks
    #

    def _on_klist__selection_changed(self, klist, selected):
        self._constant_slave.switch(selected.type)

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
        self.printers_dict = get_supported_printers()
        self._branch_station = station
        # This attribute is set to True when setup_proxies is finished
        self._is_initialized = False
        BaseEditor.__init__(self, conn, model)
        self._original_brand = self.model.brand
        self._original_model = self.model.model

    def _check_device_needs_configuration(self):
        """ Returns True if the selected device needs specifical configuration
        through the DeviceConstantsEditor, False otherwise. """
        if not self.model.is_valid() or not self.model.is_a_printer():
            return False
        # Bematech DP20C doesn't need special configuration
        return self.model.brand != "bematech" and self.model.model != "DP20C"

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
        self.setup_station_combo()
        if not self.edit_mode:
            self.is_active_button.set_sensitive(False)

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
        self.constants_button.set_sensitive(
            self._check_device_needs_configuration())

    def _edit_driver_constants(self):
        if self.model.type == DeviceSettings.FISCAL_PRINTER_DEVICE:
            self.model.create_fiscal_printer_constants()
        run_dialog(DeviceConstantsDialog, self, self.conn, self.model)

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self.setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    DeviceSettingsEditor.proxy_widgets)
        self._is_initialized = True

    def create_model(self, conn):
        return DeviceSettings(device=DeviceSettings.DEVICE_SERIAL1,
                              station=get_current_station(conn),
                              brand=None,
                              model=None,
                              type=None,
                              connection=conn)

    def get_title(self, *args):
        if self.edit_mode:
            return _("Edit Device for %s" % self.model.station.name)
        else:
            return _("Add Device")

    def validate_confirm(self):
        if not self.edit_mode:
            settings = DeviceSettings.get_by_station_and_type(
                conn=get_connection(),
                station=self.model.station.id,
                type=self.model.type)
            if settings:
                self.station.set_invalid(
                    _(u"A %s already exists for station \"%s\""
                      % (self.model.get_device_type_name(),
                         self.model.station.name)))
                return False
        return True

    # FIXME: this part will improved when bug #2334 is fixed.
    def on_confirm(self):
        if not self.model.is_a_printer():
            return self.model
        is_enabled = self.edit_mode or self.model.constants
        # FIXME: this part will be improved when bug #2641 is fixed
        is_enabled = is_enabled or (self.model.brand != "bematech"
                                    and self.model.model != "DP20C")
        if not is_enabled:
            warning( _(u"The printer will be disabled"),
                     _(u"The printer will be disabled automatically "
                        "because there are no constants defined yet."))
            self.model.inactivate()

        # Ensure that the fiscal constants are created, even if the
        # user did not click on the edit constants button
        self.model.create_fiscal_printer_constants()

        # Check if we have a virtual printer, if so we must remove it
        settings = DeviceSettings.get_virtual_printer_settings(
            self.conn, self.model.station)
        if settings:
            DeviceSettings.delete(settings.id, connection=self.conn)
        return self.model

    #
    # Kiwi callbacks
    #

    def on_brand_combo__changed(self, *args):
        self.update_model_combo()
        self._update_constants_button()
        self.refresh_ok()

    def on_type_combo__changed(self, *args):
        self.update_brand_combo()
        self._update_constants_button()
        self.refresh_ok()

    def on_brand_combo__state_changed(self, *args):
        self.update_model_combo()
        self._update_constants_button()
        self.refresh_ok()

    def on_model_combo__changed(self, *args):
        self._update_constants_button()
        self.refresh_ok()

    def on_device_combo__changed(self, *args):
        self._update_constants_button()
        self.refresh_ok()

    def on_constants_button__clicked(self, button):
        self._edit_driver_constants()
