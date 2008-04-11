# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source
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
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Gustavo Rahal               <gustavo@async.com.br>
##                  Johan Dahlin                <jdahlin@async.com.br>
##
""" Some extra methods to deal with gtk/kiwi widgets """

import gtk
from kiwi.environ import environ

# register stoq stock icons
def register_iconsets():
    icon_info = [("stoq-searchtool-icon1", "searchtool-animation1.png"),
                 ("stoq-searchtool-icon2", "searchtool-animation2.png"),
                 ("stoq-searchtool-icon3", "searchtool-animation3.png"),
                 ("stoq-searchtool-icon4", "searchtool-animation4.png"),
                 ("stoq-products", "products_24.png"),
                 ("stoq-suppliers", "kuser48px.png"),
                 ("stoq-bills", "gnome-money48px.png"),
                 ("stoq-conference", "gtk-stock-book48px.png"),
                 ("stoq-receiving", "emblem-documentation48px.png"),
                 ("stoq-transfer", "a-convert48px.png"),
                 ("stoq-clients", "config-users48px.png"),
                 ("stoq-services", "gconf-editor48px.png"),
                 ("stoq-delivery", "delivery24px.png"),
                 ("stoq-admin-app", "admin_24.png"),
                 ("stoq-pos-app", "pos_24.png"),
                 ("stoq-till-app", "till_24.png"),
                 ("stoq-stock-app", "warehouse_24.png"),
                 ("stoq-inventory-app", "inventory_24.png"),
                 ("stoq-purchase-app", "gnome-gnomine48px.png"),
                 ("stoq-sales-app", "gnome-log48px.png"),
                 ("stoq-payable-app", "gnome-money-red48px.png")]

    iconfactory = gtk.IconFactory()
    stock_ids = gtk.stock_list_ids()
    for stock_id, filename in icon_info:
        # only load image files when our stock_id is not present
        if stock_id not in stock_ids:
            filename = environ.find_resource('pixmaps', filename)
            pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
            iconset = gtk.IconSet(pixbuf)
            iconfactory.add(stock_id, iconset)
    iconfactory.add_default()

def change_toolbar_button_appearance(item, icon=None, text=None):
    button = item.get_children()[0]
    vbox = button.get_children()[0]
    image, label = vbox.get_children()
    if icon:
        image.set_from_stock(icon, gtk.ICON_SIZE_LARGE_TOOLBAR)
    if text:
        label.set_text(text)

def change_button_appearance(button, icon=None, text=None):
    alignment = button.get_children()[0]
    hbox = alignment.get_children()[0]
    image, label = hbox.get_children()
    if icon:
        image.set_from_stock(icon, gtk.ICON_SIZE_BUTTON)
    if text is not None:
        label.set_text_with_mnemonic(text)

def button_set_image_with_label(button, filename, text):
    """Sets an image above the text
    @param button:
    @param filename:
    @param text:
    """

    # Base on code in gazpacho by Lorenzo Gil Sanchez.
    button.remove(button.child)
    filename = environ.find_resource('pixmaps', filename)

    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    box = gtk.VBox()
    align.add(box)
    image = gtk.Image()
    image.set_from_file(filename)
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
