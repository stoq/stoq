# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010-2012 Async Open Source <http://www.async.com.br>
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

from storm.expr import LeftJoin, Join, Eq
from storm.references import Reference

from stoqlib.database.properties import EnumCol, IdCol, IntCol, UnicodeCol
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.events import DomainMergeEvent
from stoqlib.domain.person import Person
from stoqlib.domain.product import Product
from stoqlib.domain.views import ProductFullStockView
from stoqlib.lib.translation import stoqlib_gettext as _


class BookPublisher(Domain):
    """An institution created to publish books"""

    STATUS_ACTIVE = u'active'
    STATUS_INACTIVE = u'inactive'

    statuses = {STATUS_ACTIVE: _(u'Active'),
                STATUS_INACTIVE: _(u'Inactive')}

    __storm_table__ = 'book_publisher'

    person_id = IdCol()
    person = Reference(person_id, 'Person.id')
    status = EnumCol(allow_none=False, default=STATUS_ACTIVE)

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

    @DomainMergeEvent.connect
    @classmethod
    def on_domain_merge(cls, obj, other):
        if type(obj) != Person:
            return
        this_facet = obj.store.find(cls, person=obj).one()
        other_facet = obj.store.find(cls, person=other).one()
        if not this_facet and not other_facet:
            return
        obj.merge_facet(this_facet, other_facet)
        return set([('book_publisher', 'person_id')])


class PublisherView(Viewable):
    publiser = BookPublisher

    id = Person.id
    name = Person.name
    publisher_id = BookPublisher.id
    status = BookPublisher.status

    tables = [
        Person,
        Join(BookPublisher, Person.id == BookPublisher.person_id),
    ]

    clause = Eq(Person.merged_with_id, None)


class Book(Domain):
    """ A book class for products, holding specific data about books  """

    __storm_table__ = 'book'

    product_id = IdCol()
    product = Reference(product_id, 'Product.id')
    publisher_id = IdCol(default=None)
    publisher = Reference(publisher_id, 'BookPublisher.id')
    author = UnicodeCol(default=u'')
    series = UnicodeCol(default=u'')
    edition = UnicodeCol(default=u'')
    subject = UnicodeCol(default=u'')
    isbn = UnicodeCol(default=u'')
    language = UnicodeCol(default=u'')
    decorative_finish = UnicodeCol(default=u'')
    country = UnicodeCol(default=u'Brazil')
    pages = IntCol(default=0)
    year = IntCol(default=0)
    synopsis = UnicodeCol(default=u'')


class ProductBookFullStockView(ProductFullStockView):
    publisher = Person.name
    author = Book.author
    series = Book.series
    edition = Book.edition
    subject = Book.subject
    isbn = Book.isbn
    language = Book.language
    pages = Book.pages

    tables = ProductFullStockView.tables[:]
    tables.extend([
        Join(Book, Book.product_id == Product.id),
        LeftJoin(Person, Person.id == Book.publisher_id),
    ])

    clause = ProductFullStockView.clause
