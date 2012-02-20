# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from zope.interface import implements

from stoqlib.database.orm import IntCol, UnicodeCol, ForeignKey
from stoqlib.database.orm import LEFTJOINOn, INNERJOINOn, Viewable
from stoqlib.domain.base import Domain, ModelAdapter
from stoqlib.domain.person import Person
from stoqlib.domain.product import Product
from stoqlib.domain.views import ProductFullStockView
from stoqlib.lib.translation import stoqlib_gettext as _

from booksinterfaces import IBook

#
# Publisher person facet implementation
#


# FIXME: Rename to Publisher
class PersonAdaptToPublisher(Domain):
    """An institution created to publish books"""

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)

    statuses = {STATUS_ACTIVE: _(u'Active'),
                STATUS_INACTIVE: _(u'Inactive')}

    original = ForeignKey('Person')
    status = IntCol(default=STATUS_ACTIVE)

    #
    # IActive implementation
    #

    def inactivate(self):
        assert self.is_active, ('This person facet is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This personf facet is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.person.name

    @property
    def person(self):
        return self.original


class PublisherView(Viewable):
    columns = dict(
        id=Person.q.id,
        publisher_id=PersonAdaptToPublisher.q.id,
        name=Person.q.name,
        status=PersonAdaptToPublisher.q.status,
    )

    joins = [
        INNERJOINOn(None, PersonAdaptToPublisher,
                    Person.q.id == PersonAdaptToPublisher.q.originalID),
    ]

    @property
    def publisher(self):
        return PersonAdaptToPublisher.get(self.publisher_id,
                                          connection=self.get_connection())


#
# Book product facet implementation
#

class ProductAdaptToBook(ModelAdapter):
    implements(IBook)

    original = ForeignKey('Product')
    publisher = ForeignKey('PersonAdaptToPublisher', default=None)
    author = UnicodeCol(default='')
    series = UnicodeCol(default='')
    edition = UnicodeCol(default='')
    subject = UnicodeCol(default='')
    isbn = UnicodeCol(default='')
    language = UnicodeCol(default='')
    decorative_finish = UnicodeCol(default='')
    country = UnicodeCol(default=u'Brazil')
    pages = IntCol(default=0)
    year = IntCol(default=0)
    synopsis = UnicodeCol(default='')

Product.registerFacet(ProductAdaptToBook, IBook)


class ProductBookFullStockView(ProductFullStockView):
    columns = ProductFullStockView.columns.copy()
    columns.update(dict(
        publisher=Person.q.name,
        author=ProductAdaptToBook.q.author,
        series=ProductAdaptToBook.q.series,
        edition=ProductAdaptToBook.q.edition,
        subject=ProductAdaptToBook.q.subject,
        isbn=ProductAdaptToBook.q.isbn,
        language=ProductAdaptToBook.q.language,
        pages=ProductAdaptToBook.q.pages,
    ))
    joins = ProductFullStockView.joins[:]
    joins.extend([
        INNERJOINOn(None, ProductAdaptToBook,
                    ProductAdaptToBook.q.originalID == Product.q.id),
        LEFTJOINOn(None, Person,
                   Person.q.id == ProductAdaptToBook.q.publisherID),
    ])
    clause = ProductFullStockView.clause
