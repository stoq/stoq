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
from kiwi.environ import environ


# 16: GTK_ICON_SIZE_MENU
# 18: GTK_ICON_SIZE_SMALL_TOOLBAR
# 20: GTK_ICON_SIZE_BUTTON
# 24: GTK_ICON_SIZE_LARGE_TOOLBAR
# 32: GTK_ICON_SIZE_DND
# 48: GTK_ICON_SIZE_DIALOG

# register stoq stock icons
def register_iconsets():
    icon_info = [
        ("stoq-admin-app",
         { gtk.ICON_SIZE_MENU: "admin_16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "admin_24.png",
           gtk.ICON_SIZE_DND: "admin_32.png",
           gtk.ICON_SIZE_DIALOG: "admin_48.png" }),
        ("stoq-bills",
         { gtk.ICON_SIZE_DIALOG: "gnome-money48px.png" }),
        ("stoq-clients",
         { gtk.ICON_SIZE_DIALOG: "config-users48px.png" }),
        ("stoq-conference",
         { gtk.ICON_SIZE_DIALOG: "gtk-stock-book48px.png" }),
        ("stoq-confirm",
         { gtk.ICON_SIZE_MENU: "confirm16px.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "confirm24px.png",
           gtk.ICON_SIZE_DIALOG: "confirm48px.png" }),
        ("stoq-convert",
         { gtk.ICON_SIZE_LARGE_TOOLBAR: "a-convert24px.png",
           gtk.ICON_SIZE_DIALOG: "a-convert48px.png" }),
        ("stoq-delivery",
         { gtk.ICON_SIZE_MENU: "delivery16px.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "delivery24px.png",
           gtk.ICON_SIZE_DIALOG: "delivery48px.png" }),
        ("stoq-deliveries",
         { gtk.ICON_SIZE_LARGE_TOOLBAR: "delivery24px.png" }),
        ("stoq-hr",
         { gtk.ICON_SIZE_MENU: "hr_16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "hr_24.png",
           gtk.ICON_SIZE_DND: "hr_32.png",
           gtk.ICON_SIZE_DIALOG: "hr_48.png" }),
        ("stoq-inventory-app",
         { gtk.ICON_SIZE_LARGE_TOOLBAR: "inventory_24.png" }),
        ("stoq-lock",
         { gtk.ICON_SIZE_MENU: "panel-lockscreen16px.png" }),
        ("stoq-money",
         { gtk.ICON_SIZE_MENU: "money24px.png",
           gtk.ICON_SIZE_DIALOG: "money.png" }),
        ("stoq-payable-app",
         { gtk.ICON_SIZE_DIALOG: "gnome-money-red48px.png" }),
        ("stoq-pos-app",
         { gtk.ICON_SIZE_MENU: "pos_16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "pos_24.png",
           gtk.ICON_SIZE_DND: "pos_32.png",
           gtk.ICON_SIZE_DIALOG: "pos_48.png" }),
        ("stoq-production-app",
         { gtk.ICON_SIZE_DIALOG: "stoq-production-app.png" }),
        ("stoq-products",
         { gtk.ICON_SIZE_MENU: "products_16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "products_24.png",
           gtk.ICON_SIZE_DND: "products_32.png",
           gtk.ICON_SIZE_DIALOG: "products_48.png" }),
        ("stoq-purchase-app",
         { gtk.ICON_SIZE_DIALOG: "gnome-gnomine48px.png" }),
        ("stoq-purchase-quote",
         { gtk.ICON_SIZE_LARGE_TOOLBAR: "gnome-gnomine24px.png",
           gtk.ICON_SIZE_DIALOG: "gnome-gnomine48px.png" }),
        ("stoq-receiving",
         { gtk.ICON_SIZE_DIALOG: "emblem-documentation48px.png" }),
        ("stoq-sales-app",
         { gtk.ICON_SIZE_DIALOG: "gnome-log48px.png" }),
        ("stoq-searchtool-icon1",
         { gtk.ICON_SIZE_DIALOG:
           "searchtool-animation1.png" }),
        ("stoq-searchtool-icon2",
         { gtk.ICON_SIZE_DIALOG:
           "searchtool-animation2.png" }),
        ("stoq-searchtool-icon3",
         { gtk.ICON_SIZE_DIALOG:
         "searchtool-animation3.png" }),
        ("stoq-searchtool-icon4",
         { gtk.ICON_SIZE_DIALOG:
           "searchtool-animation4.png" }),
        ("stoq-services",
         { gtk.ICON_SIZE_DIALOG: "gconf-editor48px.png" }),
        ("stoq-stock-app",
         { gtk.ICON_SIZE_MENU: "warehouse_16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "warehouse_24.png",
           gtk.ICON_SIZE_DND: "warehouse_32.png",
           gtk.ICON_SIZE_DIALOG: "warehouse_48.png" }),
        ("stoq-suppliers",
         { gtk.ICON_SIZE_DIALOG: "kuser48px.png" }),
        ("stoq-till-app",
         { gtk.ICON_SIZE_MENU: "till_16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "till_24.png",
           gtk.ICON_SIZE_DND: "till_32.png",
           gtk.ICON_SIZE_DIALOG: "till_48.png" }),
        ("stoq-transfer",
         { gtk.ICON_SIZE_DIALOG: "a-convert48px.png" }),
        ("stoq-users",
         { gtk.ICON_SIZE_MENU: "user-small.png",
           gtk.ICON_SIZE_DIALOG: "users.png" }),
        ]

    iconfactory = gtk.IconFactory()
    stock_ids = gtk.stock_list_ids()
    for stock_id, arg in icon_info:
        # only load image files when our stock_id is not present
        if stock_id in stock_ids:
            continue
        iconset = gtk.IconSet()
        for size, filename in arg.items():
            iconsource = gtk.IconSource()
            filename = environ.find_resource('pixmaps', filename)
            iconsource.set_filename(filename)
            iconsource.set_size(size)
            iconset.add_source(iconsource)
        iconfactory.add(stock_id, iconset)
    iconfactory.add_default()

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
