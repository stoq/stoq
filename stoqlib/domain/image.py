# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Images domains"""

from zope.interface import implements

from stoqlib.database.orm import BLOBCol, UnicodeCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class Image(Domain):
    """Class responsible for storing images and it's description

    :attribute image: the image itself in a bin format
    :attribute thumbnail: the image thumbnail in a bin format
    :attribute description: the image description
    """

    (THUMBNAIL_SIZE_HEIGHT,
     THUMBNAIL_SIZE_WIDTH) = (64, 64)

    implements(IDescribable)

    image = BLOBCol(default=None)
    thumbnail = BLOBCol(default=None)
    description = UnicodeCol(default='')

    #
    #  IDescribable implementation
    #

    def get_description(self):
        if self.description:
            return self.description
        return _("Stoq image #%d" % (self.id,))
