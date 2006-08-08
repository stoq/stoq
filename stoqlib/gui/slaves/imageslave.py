# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   J. Victor Martins      <jvdm@sdf.lonestar.org>
##

""" Implementation of a generic slave for including images."""

import gtk

from kiwi.ui.dialogs import open
from kiwi.datatypes import converter

from stoqlib.domain.product import Product
from stoqlib.gui.base.editors import BaseEditorSlave
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

# TODO: Currently the database doesn't deal with pixbufs,
#       despite kiwi does. So, we are not going to use proxies
#       here, but in future changes it could be made. See #2726.
class ImageSlave(BaseEditorSlave):
    """A slave view showing a image inside a gtk.Button. When clicked
    it opens a dialog for selecting a new image, saving it on the
    'image' attribute of the model"""

    gladefile = 'ImageHolder'
    model_type = Product
    pixbuf_converter = converter.get_converter(gtk.gdk.Pixbuf)

    def __init__(self, conn, model):
        BaseEditorSlave.__init__(self, conn, model)
        self.show_image(self.pixbuf_converter.from_string(model.image))

    def show_image(self, pixbuf):
        img = gtk.Image()
        img.set_from_pixbuf(pixbuf)
        self.image.set_image(img)

    def load_image(self):
        # generating a list of suported formats extensions
        # to 'open' function
        patterns = []
        for format in gtk.gdk.pixbuf_get_formats():
            for extension in format["extensions"]:
                patterns.append('*.' + extension)
        filename = open(_("Select Image"), None, patterns)
        if not filename:
            return

        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, 64, 64)
        self.show_image(pixbuf)
        self.model.image = self.pixbuf_converter.as_string(pixbuf)

    def on_image__clicked(self, button):
        self.load_image()

