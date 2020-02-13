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

# pylint: enable=E1101

import base64

from storm.references import Reference
from zope.interface import implementer

from stoqlib.database.expr import StatementTimestamp
from stoqlib.database.properties import (IdCol, BLOBCol, UnicodeCol, BoolCol,
                                         DateTimeCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.events import (ImageCreateEvent, ImageEditEvent,
                                   ImageRemoveEvent)
from stoqlib.domain.interfaces import IDescribable
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


@implementer(IDescribable)
class Image(Domain):
    """Class responsible for storing images and it's description

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/image.html>`__

    """

    __storm_table__ = 'image'

    (THUMBNAIL_SIZE_HEIGHT,
     THUMBNAIL_SIZE_WIDTH) = (128, 128)

    #: the image itself in a bin format
    image = BLOBCol(default=None)

    #: the image thumbnail in a bin format
    thumbnail = BLOBCol(default=None)

    #: the image description
    description = UnicodeCol(default=u'')

    #: The image filename
    filename = UnicodeCol(default=u'')

    #: The date that this image was uploaded to the database
    create_date = DateTimeCol(default_factory=StatementTimestamp)

    #: Some keywords for this image
    keywords = UnicodeCol(default=u'')

    #: Some notes about the image
    notes = UnicodeCol(default=u'')

    #: If this is the main image. Only makes sense if :obj:`.sellable`
    #: is not `None`
    is_main = BoolCol(default=False)

    #: If this image is only for internal use (i.e. it won't be synchronized
    #: to any e-commerce website to be displayed publicly)
    internal_use = BoolCol(default=False)

    sellable_id = IdCol(default=None)
    #: The |sellable| that this image belongs to
    sellable = Reference(sellable_id, 'Sellable.id')

    category_id = IdCol(default=None)
    #: The |category| that this image belongs to
    category = Reference(category_id, 'SellableCategory.id')

    station_type_id = IdCol(default=None)
    #: The station type this image should be used instead of the main image.
    station_type = Reference(station_type_id, 'StationType.id')

    #
    #  Public API
    #

    def get_base64_encoded(self):
        return base64.b64encode(self.image).decode()

    #
    #  IDescribable implementation
    #

    def get_description(self):
        if self.description:
            return self.description
        return _(u"Stoq image")

    #
    #  ORMObject
    #

    @classmethod
    def delete(cls, id, store):
        image = store.get(cls, id)
        ImageRemoveEvent.emit(image)
        store.remove(image)

    #
    # Domain
    #

    def on_create(self):
        ImageCreateEvent.emit(self)

    def on_update(self):
        ImageEditEvent.emit(self)
