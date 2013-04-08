# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2013 Async Open Source
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

import gtk


class SearchFilterButton(gtk.Button):
    def __init__(self, label=None, stock=None, use_underline=True):
        gtk.Button.__init__(self, label, stock, use_underline)
        self.set_icon_size(gtk.ICON_SIZE_MENU)
        self.set_relief(gtk.RELIEF_NONE)
        if label != stock and label:
            self._set_label(label)

    def _set_label(self, label):
        self.get_children()[0].get_child().get_children()[1].set_label(label)

    def set_label_visible(self, visible):
        self.get_children()[0].get_child().get_children()[1].hide()

    def set_icon_size(self, icon_size):
        icon = self.get_children()[0].get_child().get_children()[0]
        icon.set_property('icon-size', icon_size)
