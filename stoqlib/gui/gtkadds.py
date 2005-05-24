# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
gui/gtkadds.py:

    Some extra methods to deal with gtk/kiwi widgets
"""

import gtk
import stoqlib


# register stoq stock icons
def register_iconsets(icon_info):
    iconfactory = gtk.IconFactory()
    stock_ids = gtk.stock_list_ids()
    for stock_id, file in icon_info:
        # only load image files when our stock_id is not present
        if stock_id not in stock_ids:
            pixbuf = gtk.gdk.pixbuf_new_from_file(file)
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
    if text or text == '':
        label.set_text(text)

dir = stoqlib.__path__[0] + '/gui/pixmaps/'
register_iconsets([
    ('stoq-search-pos1', dir+"searchtool-animation-pos1.png"),
    ('stoq-search-pos2', dir+"searchtool-animation-pos2.png"),
    ('stoq-search-pos3', dir+"searchtool-animation-pos3.png"),
    ('stoq-search-pos4', dir+"searchtool-animation-pos4.png"),
    ('stoq-user-small', dir+"user-small.png"),
    ('stoq-users', dir+"users.png"),
    ('stoq-sales', dir+"sales.xpm")
    ])
