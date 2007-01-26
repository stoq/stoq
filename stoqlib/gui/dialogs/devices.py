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
## Author(s):   Henrique Romano                 <henrique@async.com.br>
##
##
""" Device Settings listing dialog """

from stoqlib.gui.base.lists import AdditionListDialog
from stoqlib.gui.slaves.devicesslave import DeviceSettingsDialogSlave
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.drivers import create_virtual_printer_for_current_station
from stoqlib.domain.devices import DeviceSettings

_ = stoqlib_gettext

class DeviceSettingsDialog(AdditionListDialog):
    size = (600, 500)
    def __init__(self, conn, station=None):
        self._station = station
        AdditionListDialog.__init__(self, conn, title=_("Devices"))
        self.set_before_delete_items(self._on_delete_items)

    def _on_delete_items(self, slave, items):
        result = DeviceSettings.select(
            DeviceSettings.q.type == DeviceSettings.FISCAL_PRINTER_DEVICE,
            connection=self.conn)
        if result:
            return
        create_virtual_printer_for_current_station()
        # getting virtual printer back to this connection
        self.conn.commit()

    #
    # AdditionListDialog hooks
    #

    def get_slave(self, editor_class, columns, klist_objects):
        return DeviceSettingsDialogSlave (self.conn,
                                          station=self._station)

    def on_confirm(self):
        self.conn.commit()
        return AdditionListDialog.on_confirm(self)
