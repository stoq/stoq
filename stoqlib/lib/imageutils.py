# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2017 Async Open Source
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

"""Utilities for working with images.

Some of those functions were borrowed from datagrid_gtk3:
https://github.com/nowsecure/datagrid-gtk3/blob/master/datagrid_gtk3/utils/imageutils.py
"""

import io

from gi.repository import GdkPixbuf
from PIL import Image, ImageFilter

_image_border_size = 6
_image_shadow_size = 6
_image_shadow_offset = 2
# Generating a drop shadow is an expensive operation. Keep a cache
# of already generated drop shadows so they can be reutilized
_drop_shadows_cache = {}


def image2pixbuf(image):
    """Convert a PIL image to a pixbuf.

    :param image: the image to convert
    :type image: `PIL.Image`
    :returns: the newly created pixbuf
    :rtype: `GdkPixbuf.Pixbuf`
    """
    with io.BytesIO() as f:
        image.save(f, 'png')
        loader = GdkPixbuf.PixbufLoader.new_with_type('png')
        loader.write(f.getvalue())
        pixbuf = loader.get_pixbuf()
        loader.close()

    return pixbuf


def add_border(image, border_size=5,
               background_color=(0xff, 0xff, 0xff, 0xff)):
    """Add a border to the image.

    :param image: the image to add the border
    :type image: `PIL.Image`
    :param int border_size: the size of the border
    :param tuple background_color: the color of the border as a
        tuple containing (r, g, b, a) information
    :returns: the new image with the border
    :rtype: `PIL.Image`
    """
    width = image.size[0] + border_size * 2
    height = image.size[1] + border_size * 2

    try:
        image.convert("RGBA")
        image_parts = image.split()
        mask = image_parts[3] if len(image_parts) == 4 else None
    except IOError:  # pragma: no cover
        mask = None

    border = Image.new("RGBA", (width, height), background_color)
    border.paste(image, (border_size, border_size), mask=mask)

    return border


def add_drop_shadow(image, iterations=3, border_size=2, offset=(2, 2),
                    shadow_color=(0x00, 0x00, 0x00, 0xff)):
    """Add a drop shadow to the image.

    Based on this receipe::
        http://en.wikibooks.org/wiki/Python_Imaging_Library/Drop_Shadows

    :param image: the image to add the drop shadow
    :type image: `PIL.Image`
    :param int iterations: number of times to apply the blur filter
    :param int border_size: the size of the border to add to leave
        space for the shadow
    :param tuple offset: the offset of the shadow as (x, y)
    :param tuple shadow_color: the color of the shadow as a
        tuple containing (r, g, b, a) information
    :returns: the new image with the drop shadow
    :rtype: `PIL.Image`
    """
    width = image.size[0] + abs(offset[0]) + 2 * border_size
    height = image.size[1] + abs(offset[1]) + 2 * border_size

    key = (width, height, iterations, border_size, offset, shadow_color)
    existing_shadow = _drop_shadows_cache.get(key)
    if existing_shadow:
        shadow = existing_shadow.copy()
    else:
        shadow = Image.new('RGBA', (width, height),
                           (0xff, 0xff, 0xff, 0x00))

        # Place the shadow, with the required offset
        # if < 0, push the rest of the image right
        shadow_lft = border_size + max(offset[0], 0)
        # if < 0, push the rest of the image down
        shadow_top = border_size + max(offset[1], 0)

        shadow.paste(shadow_color,
                     [shadow_lft, shadow_top,
                      shadow_lft + image.size[0],
                      shadow_top + image.size[1]])

        # Apply the BLUR filter repeatedly
        for i in range(iterations):
            shadow = shadow.filter(ImageFilter.BLUR)

        _drop_shadows_cache[key] = shadow.copy()

    # Paste the original image on top of the shadow
    # if the shadow offset was < 0, push right
    img_lft = border_size - min(offset[0], 0)
    # if the shadow offset was < 0, push down
    img_top = border_size - min(offset[1], 0)

    shadow.paste(image, (img_lft, img_top))
    return shadow


def get_thumbnail(image_bytes, size):
    """Generate a thumbnail of the image by the given size.

    :param str image_bytes: The image bytes (e.g. the image from the database)
    :param tuple size: The size to generate the thumbnail
    :returns: The thumbnail image
    :rtype: str
    """
    with io.BytesIO(image_bytes) as f:
        im = Image.open(f)
        im.thumbnail(size, Image.BICUBIC)
        with io.BytesIO() as new_f:
            im.save(new_f, 'png')
            return new_f.getvalue()


def get_pixbuf(image_bytes, draw_border=True, fill_image=None):
    """Render image into a pixbuf doing the necessary transformations.

    :param str image_bytes: The image bytes (e.g. the image from the database)
    :param bool draw_border: if we should add a border on the image
    :param tuple fill_image: If we should fill the image with a transparent
        background to make a smaller image be at least a square of
        (size, size), with the real image at the center.
    :returns: the resized pixbuf
    :rtype: :class:`GdkPixbuf.Pixbuf`
    """
    with io.BytesIO(image_bytes) as f:
        image = Image.open(f)
        w, h = image.size

        if draw_border:
            image = add_border(image, border_size=_image_border_size)
            image = add_drop_shadow(
                image, border_size=_image_shadow_size,
                offset=(_image_shadow_offset, _image_shadow_offset))

            # After the border and the dropshadow, the size will be
            # slightly increased
            extra = ((_image_border_size * 2) +
                     (_image_shadow_size * 2) +
                     _image_shadow_offset)
            w += extra
            h += extra

        pixbuf = image2pixbuf(image)

    width = pixbuf.get_width()
    height = pixbuf.get_height()

    if fill_image is None:
        return pixbuf

    w = max(w, fill_image[0])
    h = max(h, fill_image[1])

    # Make sure the image is on the center of the image_max_size
    square_pic = GdkPixbuf.Pixbuf.new(
        GdkPixbuf.Colorspace.RGB, True, pixbuf.get_bits_per_sample(),
        w, h)
    # Fill with transparent white
    square_pic.fill(0xffffff00)

    dest_x = (w - width) / 2
    dest_y = (h - height) / 2
    pixbuf.copy_area(0, 0, width, height, square_pic, dest_x, dest_y)

    return square_pic
