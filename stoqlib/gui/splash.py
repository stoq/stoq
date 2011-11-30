# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2011 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

""" Splash screen helper """

import time

import gobject
import gtk
import pango
import pangocairo

from kiwi.component import get_utility
from kiwi.environ import environ
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.translation import stoqlib_gettext

WIDTH = 400
HEIGHT = 260
BORDER = 8 # This includes shadow out border from GtkFrame
_ = stoqlib_gettext


class SplashScreen(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)
        self.resize(WIDTH, HEIGHT)
        # Ubuntu has backported the 3.0 has-resize-grip property,
        # disable it as it doesn't make sense for splash screens
        if hasattr(self.props, 'has_resize_grip'):
            self.props.has_resize_grip = False
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.add(frame)

        darea = gtk.DrawingArea()
        darea.connect("expose-event", self.expose)
        frame.add(darea)

        self.show_all()
        filename = environ.find_resource("pixmaps", "splash.png")
        self._pixbuf = gtk.gdk.pixbuf_new_from_file(filename)

    def _get_label(self):
        info = get_utility(IAppInfo, None)
        if not info:
            return "Stoq"
        version = info.get("version")
        if ' ' in version:
            ver, rev = version.split(' ')
            version = '%s <b>%s</b>' % (ver, rev)
        return _("Version: %s") % (version, )

    def expose(self, widget, event):
        cr = widget.window.cairo_create()
        # Draw splash
        cr.set_source_pixbuf(self._pixbuf, 0, 0)
        cr.paint()

        # Draw version
        cr.set_source_rgb(.1, .1, .1)
        pcr = pangocairo.CairoContext(cr)
        layout = pcr.create_layout()
        layout.set_font_description(pango.FontDescription("Sans 14"))
        layout.set_markup(self._get_label())
        pcr.update_layout(layout)
        w, h = layout.get_pixel_size()
        cr.move_to(WIDTH - w - BORDER, HEIGHT - h - BORDER)
        pcr.show_layout(layout)

    def show(self):
        gtk.Window.show(self)

        time.sleep(0.01)
        while gtk.events_pending():
            time.sleep(0.01)
            gtk.main_iteration()


_splash = None


def show_splash():
    global _splash
    _splash = SplashScreen()
    _splash.show()


def hide_splash():
    global _splash
    if _splash:
        gobject.idle_add(_splash.destroy)
        _splash = None
