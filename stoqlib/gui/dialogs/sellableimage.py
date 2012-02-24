# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import gettext

import gtk
from kiwi.ui.delegates import GladeDelegate
from kiwi.datatypes import converter

from stoqlib.gui.base.dialogs import RunnableView

_ = gettext.gettext
_pixbuf_converter = converter.get_converter(gtk.gdk.Pixbuf)


class SellableImageViewer(GladeDelegate, RunnableView):
    title = _("Sellable Image Viewer")
    gladefile = "SellableImageViewer"
    position = (0, 0)
    size = (325, 325)

    def __init__(self, *args, **kwargs):
        GladeDelegate.__init__(self, *args, **kwargs)
        self.toplevel.set_keep_above(True)
        self.toplevel.resize(*SellableImageViewer.size)
        self.toplevel.move(*SellableImageViewer.position)
        self.sellable = None
        self.toplevel.connect("configure-event", self._on_configure)

    #
    #  Public API
    #

    def set_sellable(self, sellable):
        self.sellable = sellable
        if not self.sellable.image:
            self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                                      gtk.ICON_SIZE_DIALOG)
            return

        pixbuf = _pixbuf_converter.from_string(sellable.image.image)
        width, height = SellableImageViewer.size
        pixbuf = pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)
        self.image.set_from_pixbuf(pixbuf)

    #
    #  Private
    #

    def _on_configure(self, window, event):
        SellableImageViewer.position = event.x, event.y
        if (event.width != SellableImageViewer.size[0]
            or event.height != SellableImageViewer.size[1]):
            SellableImageViewer.size = event.width, event.height
            if self.sellable:
                self.set_sellable(self.sellable)
