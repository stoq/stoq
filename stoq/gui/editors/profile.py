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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/editors/profile.py:

    User profile editor implementation.
"""


import gettext

from kiwi.datatypes import ValidationError
from sqlobject.sqlbuilder import func, AND
from stoqlib.gui.editors import BaseEditor

from stoq.domain.profile import UserProfile
from stoq.gui.slaves.profile import UserProfileSettingsSlave
from stoq.lib.applist import get_app_descriptions
from stoq.lib.runtime import get_connection


_ = gettext.gettext

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
        apps = get_app_descriptions()
        for app_name, app_full_name, app_icon_name in apps:
            model = None
            if self.edit_mode:
                settings = self.model.profile_settings
                model = [s for s in settings if s.app_dir_name == app_name]
                if len(model) > 1:
                    raise ValueError('You should have only one instance '
                                     'for application %s' % app_name)
                if model:
                    model = model[0]
            slave = UserProfileSettingsSlave(self.conn, self.model,
                                             app_name, app_full_name,
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

