# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Attachment domain class

Allows other tables to have any kinds of attachments."""

# pylint: enable=E1101

from zope.interface import implementer

from stoqlib.database.properties import BLOBCol, UnicodeCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


@implementer(IDescribable)
class Attachment(Domain):
    __storm_table__ = 'attachment'

    #: the attachment name
    name = UnicodeCol(default=u'')

    #: MIME for the filetype attached
    mimetype = UnicodeCol(default=u'')

    #: blob that contains the file
    blob = BLOBCol(default=None)

    #
    #  IDescribable implementation
    #

    def get_description(self):
        return self.name
