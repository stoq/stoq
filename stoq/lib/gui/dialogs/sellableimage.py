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

from gi.repository import Gtk, GdkPixbuf
from kiwi.ui.delegates import GladeDelegate
from kiwi.datatypes import converter

from stoqlib.domain.image import Image
from stoq.lib.gui.base.dialogs import RunnableView
from stoqlib.lib.imageutils import get_pixbuf, get_thumbnail
from stoqlib.lib.translation import stoqlib_gettext as _

_pixbuf_converter = converter.get_converter(GdkPixbuf.Pixbuf)


class SellableImageViewer(GladeDelegate, RunnableView):
    title = _("Sellable Image Viewer")
    domain = 'stoq'
    gladefile = "SellableImageViewer"
    position = (0, 0)

    def __init__(self, size, use_thumbnail=False):
        """
        :param tuple size: the size for this viewer as (x, y)
        """
        self._use_thumbnail = use_thumbnail
        self._size = size

        GladeDelegate.__init__(self)

        self.toplevel.set_keep_above(True)
        self.toplevel.resize(*self._size)
        self.toplevel.move(*self.position)
        self.sellable = None
        self.toplevel.connect("configure-event", self._on_configure)

    #
    #  Public API
    #

    def set_sellable(self, sellable):
        self.sellable = sellable
        if not self.sellable or not self.sellable.image:
            self.image.set_from_stock(Gtk.STOCK_MISSING_IMAGE,
                                      Gtk.IconSize.DIALOG)
            return

        if self._use_thumbnail:
            size = (Image.THUMBNAIL_SIZE_WIDTH, Image.THUMBNAIL_SIZE_HEIGHT)

            if not sellable.image.thumbnail:
                # If image came without a thumbnail, generate one for it
                # This should happen only once for each image
                sellable.image.thumbnail = get_thumbnail(
                    sellable.image.image, size)

            pixbuf = get_pixbuf(sellable.image.thumbnail, size)
        else:
            pixbuf = _pixbuf_converter.from_string(sellable.image.image)
            iw, ih = pixbuf.get_width(), pixbuf.get_height()
            image_aspect = float(iw) / ih

            width, height = self._size
            window_aspect = float(width) / height

            if image_aspect < window_aspect:
                width = int(height * image_aspect)
            else:
                height = int(width / image_aspect)

            pixbuf = pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

        self.image.set_from_pixbuf(pixbuf)

    #
    #  Private
    #

    def _on_configure(self, window, event):
        self.position = event.x, event.y
        self._size = event.width, event.height
        self.set_sellable(self.sellable)
