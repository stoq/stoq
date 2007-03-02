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
##  Author(s):      Henrique Romano             <henrique@async.com.br>
##
""" Device settings slaves implementation """

from kiwi.ui.objectlist import Column
from sqlobject.sqlbuilder import AND

from stoqlib.gui.base.lists import AdditionListSlave
from stoqlib.gui.editors.deviceseditor import DeviceSettingsEditor
from stoqlib.domain.devices import DeviceSettings
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class DeviceSettingsDialogSlave(AdditionListSlave):
    def __init__(self, conn, visual_mode=False, station=None):
        self._station = station
        AdditionListSlave.__init__(self, conn,
                                   editor_class=DeviceSettingsEditor,
                                   visual_mode=visual_mode)
        if self._station is not None:
            self.register_editor_kwargs(station=self._station)
        self.connect('before-delete-items', self._before_delete_items)

    #
    # Hooks
    #

    def get_columns(self):
        return [Column('device_type_name',
                       title=_('Device Type'),
                       data_type=str,
                       sorted=True,
                       width=120),
                Column('printer_description',
                       title=_('Description'),
                       data_type=str,
                       expand=True),
                Column('station.name',
                       title=_('Station'),
                       data_type=str,
                       width=150,
                       searchable=True),
                Column('is_active',
                       title=_("Active"),
                       data_type=bool,
                       width=100)]

    def get_items(self):
        query = DeviceSettings.q.brand != 'virtual'
        if self._station:
            query = AND(query, DeviceSettings.q.stationID == self._station.id)
        return DeviceSettings.select(query, connection=self.conn)

    #
    # Callbacks
    #

    def _before_delete_items(self, list_slave, items):
        for item in items:
            DeviceSettings.delete(item.id, connection=self.conn)
        self.conn.commit()

