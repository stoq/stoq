# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
##  Author(s):      Evandro Vale Miquelito  <evandro@async.com.br>
##
"""
stoq/environ.py

    Environ variables for Stoq applications
"""

import os

from kiwi.environ import Library, environ

try:
    # We can't use from .. import ... as module until pyflakes
    # can handle it properly
    from stoq import __installed__
    config_module = __installed__
except ImportError:
    try:
        from stoq import __uninstalled__
        config_module = __uninstalled__
    except ImportError:
        raise SystemExit("FATAL ERROR: Internal error, could not load"
                         "Stoq.\n"
                         "Tried to start Stoq but critical configuration "
                         "is missing.\n")

__all__ = ['library']

library = Library('stoq', root='..')
if library.uninstalled:
    # XXX We need this since to work properly with symbolic links 
    # for stoq directories
    library.add_global_resources(sbin_dir='sbin',
                                 docs_dir='docs',
                                 pixmaps_dir='pixmaps')

def _get_dir(session_name):
    dir = getattr(config_module, session_name, None)
    if not dir:
        raise ValueError('Configuration option %s was not found' %
                         session_name)
    return dir

def _get_file_path(resource_name, file_name):
    if library.uninstalled:
        return environ.find_resource(resource_name, file_name)
    return os.path.join(_get_dir(resource_name), file_name)

def get_base_dir():
    return _get_dir('basedir')

def get_locale_dir():
    return _get_dir('locale_dir')

def get_glade_dir():
    return _get_dir('glade_dir')

def get_sbin_file_path(file_name):
    return _get_file_path('sbin_dir', file_name)

def get_pixmap_file_path(file_name):
    return _get_file_path('pixmaps_dir', file_name)

def get_docs_dir():
    if library.uninstalled:
        paths = environ.get_resource_paths('docs_dir')
        if len(paths) != 1:
            raise ValueError('It should have only one path for docs '
                             'directory, got %d instead' % len(paths))
        return paths[0]
    return os.path.join(_get_dir('docs_dir'))
