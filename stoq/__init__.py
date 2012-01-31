# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2011 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

program_name = "Stoq"
website = 'http://www.stoq.com.br'
major_version = 1
minor_version = 2
micro_version = 0
extra_version = 0
release_date = (2012, 2, 1)
stable = True

version = '%d.%d.%d' % (major_version, minor_version, micro_version)
if extra_version > 0:
    version += '.%d' % (extra_version, )

try:
    from kiwi.environ import Library
except ImportError:
    from stoq.lib.dependencies import check_dependencies
    check_dependencies()

# XXX: Use Application
library = Library('stoq')
if library.uninstalled:
    library.add_global_resource('config', 'data/config')
    library.add_global_resource('csv', 'data/csv')
    library.add_global_resource('docs', '.')
    library.add_global_resource('fonts', 'data/fonts')
    library.add_global_resource('glade', 'data/glade')
    library.add_global_resource('html', 'data/html')
    library.add_global_resource('misc', 'data/misc')
    library.add_global_resource('pixmaps', 'data/pixmaps')
    library.add_global_resource('sql', 'data/sql')
    library.add_global_resource('template', 'data/template')
    library.add_global_resource('uixml', 'data/uixml')
    library.add_resource('plugin', 'plugins')

library.enable_translation()
library.set_application_domain('stoq')
