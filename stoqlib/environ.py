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
stoq/lib/environ.py

    Environ variables
"""

from kiwi.environ import environ

try:
    # We can't use from .. import ... as module until pyflakes
    # can handle it properly
    from stoqlib import __installed__
    config_module = __installed__
except ImportError:
    try:
        from stoqlib import __uninstalled__
        config_module = __uninstalled__
    except ImportError:
        raise SystemExit("FATAL ERROR: Internal error, could not load"
                         "stoqlib.\n"
                         "Tried to load stoqlib but critical configuration "
                         "is missing.\n")


def get_pixmaps_dir():
    return getattr(config_module, 'pixmap_dir')

def get_glade_dir():
    return getattr(config_module, 'glade_dir')
