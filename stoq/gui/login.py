# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
""" Login dialog for users authentication"""

import gettext

import gtk
from kiwi.ui.delegates import SlaveDelegate
from kiwi.ui.widgets.list import Column
from kiwi.python import Settable
from stoqlib.gui.login import LoginDialog

from stoq.lib.applist import get_app_descriptions

_ = gettext.gettext


class StoqLoginDialog(LoginDialog):
    def __init__(self, title=None, choose_applications=True):
        LoginDialog.__init__(self, title)
        self.choose_applications = choose_applications
        if self.choose_applications:
            self.slave = SelectApplicationsSlave()
            self.attach_slave('applist_holder', self.slave)
            self.size = 450, 250
            self.get_toplevel().set_size_request(*self.size)
                    

    def get_app_name(self):
        if self.choose_applications:
            selected = self.slave.klist.get_selected()
            return selected.app_name
        return None


class SelectApplicationsSlave(SlaveDelegate):
    gladefile = "SelectApplicationsSlave"

    def __init__(self):
        SlaveDelegate.__init__(self, gladefile=self.gladefile)
        self._setup_applist()

    def _setup_applist(self):
        self.klist.get_treeview().set_headers_visible(False)
        self.klist.set_columns(self._get_columns())

        apps = get_app_descriptions()
        # sorting by app_full_name
        apps = [(app_full_name, app_name, app_icon_name) 
                    for app_name, app_full_name, app_icon_name in apps]
        apps.sort()
        for app_full_name, app_name, app_icon_name in apps:
            model = Settable(app_name=app_name, app_full_name=app_full_name, 
                             icon_name=app_icon_name)
            self.klist.append(model)
        if not len(self.klist):
            raise ValueError('Application list should have items at '
                             'this point')
        self.klist.select(self.klist[0])
        self.app_list.show()

    def _get_columns(self):
        return [Column('icon_name', use_stock=True, 
                       justify=gtk.JUSTIFY_LEFT, expand=True,
                       icon_size=gtk.ICON_SIZE_LARGE_TOOLBAR),
                Column('app_full_name', data_type=str, 
                       expand=True)]
