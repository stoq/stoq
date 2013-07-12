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

# pylint: enable=E1101

from storm.references import Reference
from zope.interface import implementer

from stoqlib.domain.base import Domain
from stoqlib.database.properties import DateTimeCol, UnicodeCol, IdCol
from stoqlib.domain.interfaces import IDescribable
from stoqlib.lib.dateutils import localnow


@implementer(IDescribable)
class PaymentComment(Domain):
    __storm_table__ = 'payment_comment'

    author_id = IdCol()
    author = Reference(author_id, 'LoginUser.id')
    payment_id = IdCol()
    payment = Reference(payment_id, 'Payment.id')
    date = DateTimeCol(default_factory=localnow)
    comment = UnicodeCol()

    #
    # IDescribable implementation
    #

    def get_description(self):
        return u"[%s] %s" % (self.author.person.name, self.comment)
