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

import mock

from stoqlib.domain.devices import DeviceSettings
from stoqlib.gui.editors.deviceseditor import DeviceSettingsEditor
from stoqlib.gui.test.uitestutils import GUITest


class _Device(object):
    def __init__(self, name):
        self.device_name = name


class TestDeviceSettingsEditor(GUITest):
    @mock.patch('stoqlib.gui.editors.deviceseditor.DeviceManager.get_serial_devices')
    def test_create(self, get_serial_devices):
        get_serial_devices.return_value = [_Device('/dev/ttyS0'),
                                           _Device('/dev/ttyS1')]
        station = self.create_station()
        editor = DeviceSettingsEditor(self.store, station=station)
        editor.type_combo.select_item_by_data(DeviceSettings.SCALE_DEVICE)
        editor.brand_combo.select_item_by_data('toledo')
        self.check_editor(editor, 'editor-devicesetting-create')

    @mock.patch('stoqlib.gui.editors.deviceseditor.DeviceManager.get_serial_devices')
    def test_show(self, get_serial_devices):
        get_serial_devices.return_value = [_Device('/dev/ttyS0'),
                                           _Device('/dev/ttyS1')]
        station = self.create_station()
        settings = DeviceSettings(store=self.store,
                                  type=DeviceSettings.SCALE_DEVICE)
        editor = DeviceSettingsEditor(self.store, model=settings,
                                      station=station)
        self.check_editor(editor, 'editor-devicesetting-show')
