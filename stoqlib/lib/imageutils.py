# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source
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
##
""" Utility class and functions for images """

import imghdr
import tempfile
import os.path

import gobject


class ImageHelper(object):

    def __init__(self, image_path):
        self.image_path = image_path
        self._image = None

    def _save_image(self):
        if self._image is not None:
            tmp_file = tempfile.NamedTemporaryFile(delete=False,
                                                   prefix='stoqlib-logo')
            tmp_file.close()

            self._image.save(tmp_file.name, self._get_image_type())
            self.image_path = tmp_file.name

    def _check_image_type(self):
        # types supported by gtk.gdk.Pixbuf
        return self._get_image_type() in ["jpeg", "png"]

    def _get_image_type(self):
        if os.path.exists(self.image_path):
            return imghdr.what(str(self.image_path))

    #
    # Public API
    #

    def is_valid(self):
        """Returns True if the image is supported by Stoq, False
        otherwise.
        """
        import gtk
        # FIXME: self._image should not be created here. As the name
        #        of this method says, it should only check for valid
        #        images.
        #        We should either rename this method name and change
        #        the logic to do what it's doing now, or create a new
        #        one to do that and make this behave like it should.
        try:
            if not self._check_image_type():
                return False
            self._image = gtk.gdk.pixbuf_new_from_file(self.image_path)
        except gobject.GError:
            return False

        return True

    def resize(self, size):
        if not self.is_valid():
            return
        import gtk
        current_size = self._image.get_width(), self._image.get_height()
        if current_size != size:
            w, h = size
            self._image = self._image.scale_simple(
                w, h, gtk.gdk.INTERP_BILINEAR)
            self._save_image()
