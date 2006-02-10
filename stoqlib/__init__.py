# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
##
## Author(s):       Johan Dahlin <jdahlin@async.com.br>
##

from kiwi.environ import Library

__program_name__    = "Stoqlib"
__website__         = 'http://www.stoq.com.br'
__version__         = "0.6.0"
__release_date__    = (2006, 1, 27)


__all__ = ['library']

library = Library('stoqlib', root='..')
if library.uninstalled:
    # XXX: Move this to enable_translation()
    try:
        library.add_resources(locale='locale')
    except EnvironmentError:
        pass
    library.add_global_resources(pixmaps='data/pixmaps',
                                 glade='data',
                                 fonts='data/fonts')
library.enable_translation()

