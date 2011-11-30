# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import gtk


def _foreach_child(widget, cb, lvl=0):
    cb(widget, lvl)
    if isinstance(widget, gtk.Container):
        for child in widget.get_children():
            _foreach_child(child, cb, lvl + 1)


def introspect_slaves(window):
    """Traverses all the children of window and prints out all the
    kiwi slaves.
    @param window: a gtk.Window subclass
    """
    print 'Analyzing', window

    def _printone(slave, lvl=0):
        filename = slave.gladefile + '.glade'
        print ' ' * lvl, slave.__class__.__name__, filename

    def _parse(widget, lvl):
        if isinstance(widget, gtk.EventBox):
            slave = widget.get_data('kiwi::slave')
            if slave is not None:
                _printone(slave, lvl)

    _foreach_child(window, _parse)
