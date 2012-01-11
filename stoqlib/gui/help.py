# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Showing help.  """

import os

import gtk

import stoqlib
from stoqlib.gui.base.dialogs import get_current_toplevel


def show_contents(screen=None):
    show_section('', screen=screen)


def show_section(section, screen=None):
    if stoqlib.library.uninstalled:
        root = stoqlib.library.get_root()
        uri = os.path.join(root, 'help', 'pt_BR')
        if section != '':
            uri += '/' + section + '.page'
    else:
        uri = 'stoq'
        if section != '':
            uri += '?' + section

    if not screen:
        toplevel = get_current_toplevel()
        if toplevel:
            screen = toplevel.get_screen()

    gtk.show_uri(screen, 'ghelp:' + uri, gtk.get_current_event_time())
