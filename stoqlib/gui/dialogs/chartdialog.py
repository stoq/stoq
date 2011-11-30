# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Chart Generation Dialog """

import gtk
import webkit

from twisted.internet import reactor


class ChartDialog(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.connect('destroy', lambda x: reactor.stop())
        self.set_size_request(800, 480)
        self._view = webkit.WebView()
        self.add(self._view)
        self.set_title("Chart")
        self.open_chart('MonthlyPaymentsChart', year=2009)

    def open_chart(self, name, **kwargs):
        port = 8080
        url = 'http://localhost:%d/chart?name=%s&' % (port, name)
        for key, value in kwargs.items():
            url += key + '=' + str(value)
        self._view.load_uri(url)
