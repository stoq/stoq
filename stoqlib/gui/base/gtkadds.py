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
         { gtk.ICON_SIZE_MENU: "stoq-admin-16x16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-admin-24x24.png",
           gtk.ICON_SIZE_DND: "stoq-admin-32x32.png",
           gtk.ICON_SIZE_DIALOG: "stoq-admin-48x48.png" }),
        ("stoq-bills",
         { gtk.ICON_SIZE_DIALOG: "stoq-bills-48x48.png" }),
        ("stoq-clients",
         { gtk.ICON_SIZE_DIALOG: "stoq-clients-48x48.png" }),
        ("stoq-edit",
         { gtk.ICON_SIZE_DIALOG: "stoq-edit-48x48.png" }),
        ("stoq-delivery",
         { gtk.ICON_SIZE_MENU: "stoq-delivery-16x16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-delivery-24x24.png",
           gtk.ICON_SIZE_DIALOG: "stoq-delivery-48x48.png" }),
        ("stoq-hr",
         { gtk.ICON_SIZE_MENU: "stoq-hr-16x16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-hr-24x24.png",
           gtk.ICON_SIZE_DND: "stoq-hr-32x32.png",
           gtk.ICON_SIZE_DIALOG: "stoq-hr-48x48.png" }),
        ("stoq-inventory-app",
         { gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-inventory-app-24x24.png",
           gtk.ICON_SIZE_DIALOG: "stoq-inventory-app-48x48.png" }),
        ("stoq-money",
         { gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-money-24x24.png",
           gtk.ICON_SIZE_DIALOG: "stoq-money-48x48.png" }),
        ("stoq-money-add",
         { gtk.ICON_SIZE_MENU: "stoq-money-add-16x16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-money-add-24x24.png" }),
        ("stoq-money-remove",
         { gtk.ICON_SIZE_MENU: "stoq-money-remove-16x16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-money-remove-24x24.png" }),
        ("stoq-payable-app",
         { gtk.ICON_SIZE_DIALOG: "stoq-payable-app-48x48.png" }),
        ("stoq-pos-app",
         { gtk.ICON_SIZE_MENU: "stoq-pos-app-16x16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-pos-app-24x24.png",
           gtk.ICON_SIZE_DND: "stoq-pos-app-32x32.png",
           gtk.ICON_SIZE_DIALOG: "stoq-pos-app-48x48.png" }),
        ("stoq-production-app",
         { gtk.ICON_SIZE_DIALOG: "stoq-production-app.png" }),
        ("stoq-products",
         { gtk.ICON_SIZE_MENU: "stoq-products-16x16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-products-24x24.png",
           gtk.ICON_SIZE_DND: "stoq-products-32x32.png",
           gtk.ICON_SIZE_DIALOG: "stoq-products-48x48.png" }),
        ("stoq-purchase-app",
        { gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-purchase-app-24x24.png",
          gtk.ICON_SIZE_DIALOG: "stoq-purchase-app-48x48.png" }),
        ("stoq-receiving",
         { gtk.ICON_SIZE_DIALOG: "stoq-receiving-48x48.png" }),
        ("stoq-sales-app",
         { gtk.ICON_SIZE_DIALOG: "stoq-sales-app-48x48.png" }),
        ("stoq-services",
         { gtk.ICON_SIZE_DIALOG: "stoq-services-48x48.png" }),
        ("stoq-stock-app",
         { gtk.ICON_SIZE_MENU: "stoq-stock-app-16x16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-stock-app-24x24.png",
           gtk.ICON_SIZE_DND: "stoq-stock-app-32x32.png",
           gtk.ICON_SIZE_DIALOG: "stoq-stock-app-48x48.png" }),
        ("stoq-suppliers",
         { gtk.ICON_SIZE_DIALOG: "stoq-suppliers-48x48.png" }),
        ("stoq-till-app",
         { gtk.ICON_SIZE_MENU: "stoq-till-app-16x16.png",
           gtk.ICON_SIZE_LARGE_TOOLBAR: "stoq-till-app-24x24.png",
           gtk.ICON_SIZE_DND: "stoq-till-app-32x32.png",
           gtk.ICON_SIZE_DIALOG: "stoq-till-app-48x48.png" }),
        ("stoq-users",
         { gtk.ICON_SIZE_MENU: "stoq-users-16x16.png",
           gtk.ICON_SIZE_DIALOG: "stoq-users-48x48.png" }),
        ("stoq-system",
         { gtk.ICON_SIZE_DIALOG: "stoq-system-48x48.png" }),
        ("stoq-calc",
         { gtk.ICON_SIZE_DIALOG: "stoq-calc-48x48.png" }),
        ("stoq-taxes",
         { gtk.ICON_SIZE_DIALOG: "stoq-taxes-48x48.png" }),
        ("stoq-devices",
         { gtk.ICON_SIZE_DIALOG: "stoq-devices-48x48.png" }),
        ("stoq-user-profiles",
         { gtk.ICON_SIZE_DIALOG: "stoq-user-profiles-48x48.png" }),
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