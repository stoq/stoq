# -*- Mode: Python; coding: utf-8 -*-
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

import glib
import gtk
import pango
import pangocairo

from kiwi.component import get_utility
from kiwi.environ import environ
from kiwi.ui.pixbufutils import pixbuf_from_string
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.translation import stoqlib_gettext

WIDTH = 462
HEIGHT = 260
BORDER = 8  # This includes shadow out border from GtkFrame
_WINDOW_TIMEOUT = 100  # How often we should check if there are
                      # other visible windows

_ = stoqlib_gettext


class SplashScreen(gtk.Window):

    def __init__(self):
        gtk.Window.__init__(self)
        self.set_name('SplashWindow')
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)
        self.resize(WIDTH, HEIGHT)
        # Ubuntu has backported the 3.0 has-resize-grip property,
        # disable it as it doesn't make sense for splash screens
        if hasattr(self.props, 'has_resize_grip'):
            self.props.has_resize_grip = False

        darea = gtk.DrawingArea()
        try:
            darea.connect("expose-event", self.expose)
        except TypeError:
            darea.connect("draw", self.draw)
        self.add(darea)

        self.show_all()
        pixbuf_data = environ.get_resource_string("stoq", "pixmaps", "splash.png")
        self._pixbuf = pixbuf_from_string(pixbuf_data)

        glib.timeout_add(_WINDOW_TIMEOUT, self._hide_splash_timeout)

    def _hide_splash_timeout(self):
        # Hide the splash screen as soon as there is another window
        # created
        if len(gtk.window_list_toplevels()) > 1:
            self.destroy()
            return False
        return True

    def _get_label(self):
        info = get_utility(IAppInfo, None)
        if not info:
            return "Stoq"
        version = info.get("version")
        if ' ' in version:
            ver, rev = version.split(' ')
            version = '%s\n<span font="8">%s</span>' % (ver, glib.markup_escape_text(rev))
        return _("Version %s") % (version, )

    def _draw_gi(self, cr):
        gtk.gdk.cairo_set_source_pixbuf(cr, self._pixbuf, 0, 0)
        cr.paint()

        cr.set_source_rgb(.8, .8, .8)
        layout = pangocairo.create_layout(cr)
        desc = pango.FontDescription('Sans 12')
        layout.set_font_description(desc)
        layout.set_alignment(pango.ALIGN_CENTER)
        layout.set_markup(self._get_label(), -1)
        pangocairo.update_layout(cr, layout)
        w, h = layout.get_pixel_size()
        cr.move_to((WIDTH - w) / 2, (HEIGHT / 2) + h)
        pangocairo.show_layout(cr, layout)

    def draw(self, widget, cr):
        self._draw_gi(cr)

    def expose(self, widget, event):
        cr = widget.window.cairo_create()
        if not hasattr(cr, 'set_source_pixbuf'):
            self._draw_gi(cr)
            return
        # Draw splash
        cr.set_source_pixbuf(self._pixbuf, 0, 0)
        cr.paint()

        # Draw version
        cr.set_source_rgb(1, 1, 1)
        pcr = pangocairo.CairoContext(cr)
        layout = pcr.create_layout()
        layout.set_alignment(pango.ALIGN_CENTER)
        layout.set_font_description(pango.FontDescription("Sans 10"))
        layout.set_markup(self._get_label())
        pcr.update_layout(layout)
        w, h = layout.get_pixel_size()
        cr.move_to((WIDTH - w) / 1.09, (HEIGHT / 2) + h)
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
