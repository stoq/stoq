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

import gtk
from kiwi.component import get_utility
from kiwi.datatypes import ValidationError
from kiwi.ui.widgets.checkbutton import ProxyCheckButton
from sqlobject.sqlbuilder import func, AND

from stoqlib.database.runtime import get_connection
from stoqlib.domain.profile import UserProfile
from stoqlib.gui.base.editors import BaseEditor
from stoqlib.lib.interfaces import IApplicationDescriptions
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class UserProfileEditor(BaseEditor):
    model_name = _('User Profile')
    model_type = UserProfile
    gladefile = 'UserProfileEditor'
    proxy_widgets = ('profile_name', )

    #
    # BaseEditor Hooks
    #

    def create_model(self, conn):
        return UserProfile(name='', connection=conn)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    UserProfileEditor.proxy_widgets)
        self.set_description(self.model.name)

    def setup_slaves(self):
        settings = {}
        for setting in self.model.profile_settings:
            settings[setting.app_dir_name] = setting

        apps = get_utility(IApplicationDescriptions)
        for name, full_name, icon_name in apps.get_descriptions():
            # Create the user interface for each application which is
            # a HBox, a CheckButton and an Image
            box = gtk.HBox()
            box.show()

            button = ProxyCheckButton()
            button.set_label(full_name)
            button.data_type = bool
            button.model_attribute = 'has_permission'
            button.show()
            box.pack_start(button, padding=6)

            image = gtk.image_new_from_stock(icon_name, gtk.ICON_SIZE_MENU)
            box.pack_start(image, False, False)
            image.show()

            self.applications_vbox.pack_start(box, False)

            if self.edit_mode:
                if not name in settings:
                    raise AssertionError("Unknown application: %s" % name)
                model = settings[name]
            else:
                model = None

            setattr(self, name, button)
            self.add_proxy(model, [name])

        # Scroll to the bottom of the scrolled window
        vadj = self.scrolled_window.get_vadjustment()
        vadj.set_value(vadj.upper)

    #
    # Kiwi handlers
    #

    def on_profile_name__validate(self, widget, value):
        conn = get_connection()
        q1 = func.UPPER(UserProfile.q.name) == value.upper()
        q2 = UserProfile.q.id != self.model.id
        query = AND(q1, q2)
        if UserProfile.select(query, connection=conn):
            return ValidationError('This profile already exists!')
