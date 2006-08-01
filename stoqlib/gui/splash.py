# -*- Mode: Python; coding: iso-8859-1 -*-
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Johan Dahlin   <jdahlin@async.com.br>
##

""" Splash screen helper """

import time

import gtk

class SplashScreen(object):
    def __init__(self, filename):
        self._filename = filename
        self._window = self._construct()

    def _construct(self):
        gtkimage = gtk.Image()
        gtkimage.set_from_file(self._filename)
        gtkimage.show()
        w = gtk.Window()
        f = gtk.Frame()
        f.set_property('shadow-type', gtk.SHADOW_OUT)
        w.add(f)
        f.show()
        w.set_decorated(False)
        f.add(gtkimage)
        w.set_position(gtk.WIN_POS_CENTER)
        w.show_now()
        return w

    def show(self):
        self._window.show()

        time.sleep(0.01)
        while gtk.events_pending():
            time.sleep(0.01)
            gtk.main_iteration()

    def hide(self):
        self._window.destroy()
