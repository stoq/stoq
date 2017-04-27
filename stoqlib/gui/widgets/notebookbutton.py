# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2013 Async Open Source
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

from gi.repository import Gtk, GObject


class NotebookCloseButton(Gtk.Button):
    """A simple button that doesn't have much border or padding, to be used
    specially with notebooks.
    """
    __gtype_name__ = 'NotebookCloseButton'

    def __init__(self):
        super(NotebookCloseButton, self).__init__()

        self.set_relief(Gtk.ReliefStyle.NONE)
        image = Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU)
        self.add(image)


GObject.type_register(NotebookCloseButton)
