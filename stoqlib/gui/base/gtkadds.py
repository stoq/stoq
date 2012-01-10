# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source
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
""" Some extra methods to deal with gtk/kiwi widgets """

import gtk


def change_button_appearance(button, icon=None, text=None):
    alignment = button.get_children()[0]
    hbox = alignment.get_children()[0]
    image, label = hbox.get_children()
    if icon:
        image.set_from_stock(icon, gtk.ICON_SIZE_BUTTON)
    if text is not None:
        label.set_text_with_mnemonic(text)


def button_set_image_with_label(button, stock_id, text):
    """Sets an image above the text
    @param button:
    @param stock_id:
    @param text:
    """

    # Base on code in gazpacho by Lorenzo Gil Sanchez.
    if button.child:
        button.remove(button.child)

    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    box = gtk.VBox()
    align.add(box)
    image = gtk.Image()
    image.set_from_stock(stock_id, gtk.ICON_SIZE_LARGE_TOOLBAR)
    label = gtk.Label(text)
    if '_' in text:
        label.set_use_underline(True)

    box.pack_start(image)
    box.pack_start(label)

    align.show_all()
    button.add(align)


_pixbuf_cache = {}


def render_pixbuf(color_name):
    if color_name is None:
        return None

    pixbuf = _pixbuf_cache.get(color_name)
    if pixbuf is not None:
        return pixbuf

    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 16, 16)
    color = gtk.gdk.color_parse(color_name)
    rgb = (((color.red / 256) << 24) +
           ((color.green / 256) << 16) +
           ((color.blue / 256) << 8)) + 0xff
    pixbuf.fill(rgb)
    _pixbuf_cache[color_name] = pixbuf
    return pixbuf
