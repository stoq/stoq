# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006, 2007 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##

program_name    = "Stoq"
website         = 'http://www.stoq.com.br'
version         = "0.9.6"
release_date    = (2008, 03, 18)

try:
    from kiwi.environ import Library
except ImportError:
    raise SystemExit("Could not find kiwi")

# XXX: Use Application
lib = Library('stoq')
if lib.uninstalled:
    lib.add_global_resource('pixmaps', 'data/pixmaps')
    lib.add_global_resource('glade', 'data/glade')
    lib.add_global_resource('config', 'data/config')
    lib.add_global_resource('docs', '.')
lib.enable_translation()
lib.set_application_domain('stoq')
