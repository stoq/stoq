# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006, 2007 Async Open Source
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
## Author(s):       Johan Dahlin                <jdahlin@async.com.br>
##                  Evandro Vale Miquelito      <evandro@async.com.br>
##
##

import os
import sys

from kiwi.environ import Library

program_name    = "Stoqlib"
website         = 'http://www.stoq.com.br/'
version         = "0.9.5"
db_version      = 11
release_date    = (2008, 03, 18)

__all__ = ['library']

library = Library('stoqlib', root='..')
if library.uninstalled:
    library.add_global_resources(pixmaps='data/pixmaps',
                                 sql='data/sql',
                                 glade='data/glade',
                                 fonts='data/fonts',
                                 csv='data/csv',
                                 template='data/template',)
    library.add_resource('plugin', 'plugins')
    externals = os.path.join(library.get_root(), 'external')
else:
    # root = $prefix/lib/pythonX.Y/site-packages
    # We want $prefix/lib/stoqlib, eg ../../stoqlib
    externals = os.path.join(library.prefix, 'lib', 'stoqlib')
sys.path.insert(0, externals)
library.enable_translation()
