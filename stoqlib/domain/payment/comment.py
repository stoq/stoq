# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source
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
""" Payment comment implementations."""

import datetime

from zope.interface import implements

from stoqlib.domain.base import Domain
from stoqlib.database.orm import ForeignKey, DateTimeCol, UnicodeCol
from stoqlib.domain.interfaces import IDescribable


class PaymentComment(Domain):
    author = ForeignKey('PersonAdaptToUser')
    payment = ForeignKey('Payment')
    date = DateTimeCol(default=datetime.datetime.now)
    comment = UnicodeCol()

    implements(IDescribable)

    #
    # IDescribable implementation
    #

    def get_description(self):
        return "[%s] %s" % (self.author.person.name, self.comment)
