# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2012 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

"""Stoqlib API

Singleton object which makes it easier to common stoqlib APIs without
having to import their symbols.
"""

from stoqlib.lib.component import get_utility

from stoqlib.database.runtime import new_store, get_default_store
from stoqlib.database.runtime import get_current_branch, get_current_station, get_current_user
from stoqlib.database.settings import db_settings
from stoqlib.lib.devicemanager import DeviceManager
from stoqlib.lib.environment import is_developer_mode
from stoqlib.lib.interfaces import IStoqConfig
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.settings import get_settings
from stoqlib.l10n.l10n import get_l10n_field


class safe_str(str):
    pass


class StoqAPI(object):
    def get_default_store(self):
        return get_default_store()

    def new_store(self):
        return new_store()

    def get_current_branch(self, store):
        return get_current_branch(store)

    def get_current_station(self, store):
        return get_current_station(store)

    def get_current_user(self, store):
        return get_current_user(store)

    @property
    def config(self):
        return get_utility(IStoqConfig)

    @property
    def db_settings(self):
        return db_settings

    @property
    def user_settings(self):
        return get_settings()

    @property
    def device_manager(self):
        return DeviceManager.get_instance()

    def is_developer_mode(self):
        return is_developer_mode()

    def get_l10n_field(self, field_name, country=None):
        return get_l10n_field(field_name, country=country)


api = StoqAPI()
api.sysparam = sysparam
