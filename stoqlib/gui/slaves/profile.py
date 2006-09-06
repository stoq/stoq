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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
""" User profile slaves implementation"""

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.editors import BaseEditorSlave
from stoqlib.domain.profile import ProfileSettings, UserProfile

_ = stoqlib_gettext

class UserProfileSettingsSlave(BaseEditorSlave):
    model_type = ProfileSettings
    gladefile = 'UserProfileSettingsSlave'
    proxy_widgets = ('has_permission', )

    def __init__(self, conn, profile, app_name, app_full_name, model=None):
        self.profile = profile
        self.app_name = app_name
        BaseEditorSlave.__init__(self, conn, model)
        self.profile_name.set_text(app_full_name)

    #
    # BaseEditor Hooks
    #

    def get_title_model_attribute(self, model):
        return model.name

    def create_model(self, conn):
        if not (self.profile and isinstance(self.profile, UserProfile)):
            raise ValueError('You must specify a valid profile')
        if not self.app_name:
            raise ValueError('You must specify an application name')
        return ProfileSettings(connection=conn,
                               app_dir_name=self.app_name,
                               has_permission=True,
                               user_profile=self.profile)

    def setup_proxies(self):
        data = self.model.has_permission
        self.proxy = self.add_proxy(
            self.model, UserProfileSettingsSlave.proxy_widgets)
