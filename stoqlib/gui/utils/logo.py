# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

from kiwi.environ import environ
from kiwi.ui.pixbufutils import pixbuf_from_string

sizes = {
    'config': (100, 32),
    'login': (188, 60),
    'about': (188, 60),
    'pos': (100, 32),
    'update': (188, 60),
}


def render_logo_pixbuf(size):
    width, height = sizes.get(size, (100, 32))
    logo = environ.get_resource_string('stoq', 'pixmaps', 'stoq_logo.svg')
    return pixbuf_from_string(logo, 'svg', width=width, height=height)
