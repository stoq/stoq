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
""" User profile editor implementation.  """

from kiwi.datatypes import ValidationError
from kiwi.component import get_utility
from sqlobject.sqlbuilder import func, AND

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.profile import UserProfile
from stoqlib.gui.interfaces import IApplicationDescriptions
from stoqlib.gui.base.editors import BaseEditor
from stoqlib.gui.slaves.profile import UserProfileSettingsSlave
from stoqlib.lib.runtime import get_connection


_ = stoqlib_gettext


class UserProfileEditor(BaseEditor):
    model_name = _('User Profile')
    model_type = UserProfile
    gladefile = 'UserProfileEditor'
    proxy_widgets = ('profile_name', )

    #
    # BaseEditor Hooks
    #

    def get_title_model_attribute(self, model):
        return model.name

    def create_model(self, conn):
        return UserProfile(name='', connection=conn)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    UserProfileEditor.proxy_widgets)

    def setup_slaves(self):
        apps = get_utility(IApplicationDescriptions)
        for name, full_name, icon_name in apps.get_descriptions():
            model = None
            if self.edit_mode:
                settings = self.model.profile_settings
                model = [s for s in settings if s.app_dir_name == name]
                if len(model) > 1:
                    raise ValueError('You should have only one instance '
                                     'for application %s' % name)
                if model:
                    model = model[0]
            slave = UserProfileSettingsSlave(self.conn, self.model,
                                             name, full_name,
                                             model=model)
            widget = slave.get_toplevel()
            self.applications_vbox.pack_start(widget, False)
            # Scroll to the bottom of the scrolled window
            vadj = self.scrolled_window.get_vadjustment()
            vadj.set_value(vadj.upper)
            widget.show()

    #
    # Kiwi handlers
    #
    
    def on_profile_name__validate(self, widget, value):
        conn = get_connection()
        q1 = func.UPPER(UserProfile.q.name) == value.upper()
        q2 = UserProfile.q.id != self.model.id
        query = AND(q1, q2)
        if UserProfile.select(query, connection=conn).count():
            return ValidationError('This profile already exists!')
