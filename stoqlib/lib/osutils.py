# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import os
import platform

_system = platform.system()

def get_application_dir(appname="stoq"):
    """Fetches a application specific directory,
    this can be used to save temporary files and other state.
    This also creates the directory if it doesn't exist
    @returns: the application directory
    """
    if _system == 'Linux':
        appdir = os.path.join(os.environ['HOME'], '.' + appname)
    elif _system == 'Windows':
        appdir = os.path.join(os.environ['APPDATA'], appname)
    else:
        raise SystemExit("unknown system: %s" % (system, ))
    if not os.path.exists(appdir):
        os.makedirs(appdir)
    return appdir

def get_username():
    """@returns: the current username"""
    if _system == 'Linux':
        return os.environ['USER']
    elif _system == 'Windows':
        return os.environ['USERNAME']
    else:
        raise SystemExit("unknown system: %s" % (system, ))
