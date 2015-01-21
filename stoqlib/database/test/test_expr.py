# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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

"""Tests for module :class:`stoqlib.database.viewable.Viewable`"""

import datetime

from storm.expr import Cast

from stoqlib.database.expr import Case, Between, GenerateSeries, Field
from stoqlib.domain.event import Event
from stoqlib.domain.test.domaintest import DomainTest


class ViewableTest(DomainTest):

    def test_between(self):
        self.clean_domain([Event])

        a = datetime.date(2012, 1, 5)
        b = datetime.date(2012, 1, 10)
        query = Between(Event.date, a, b)
        self.assertEquals(self.store.find(Event, query).count(), 0)

        Event(store=self.store, date=datetime.datetime(2012, 1, 4),
              event_type=Event.TYPE_SYSTEM, description=u'')
        self.assertEquals(self.store.find(Event, query).count(), 0)

        Event(store=self.store, date=datetime.datetime(2012, 1, 5),
              event_type=Event.TYPE_SYSTEM, description=u'')
        self.assertEquals(self.store.find(Event, query).count(), 1)

        Event(store=self.store, date=datetime.datetime(2012, 1, 10),
              event_type=Event.TYPE_SYSTEM, description=u'')
        self.assertEquals(self.store.find(Event, query).count(), 2)

        Event(store=self.store, date=datetime.datetime(2012, 1, 11),
              event_type=Event.TYPE_SYSTEM, description=u'')
        self.assertEquals(self.store.find(Event, query).count(), 2)

    def test_generate_series_date(self):
        a = datetime.datetime(2012, 1, 1)
        b = datetime.datetime(2012, 4, 1)
        series = GenerateSeries(Cast(a, 'timestamp'),
                                Cast(b, 'timestamp'),
                                Cast(u'1 month', 'interval')),

        data = list(self.store.using(series).find(Field('generate_series', 'generate_series')))
        self.assertEquals(len(data), 4)

        self.assertEquals(data[0], a)
        self.assertEquals(data[1], datetime.datetime(2012, 2, 1))
        self.assertEquals(data[2], datetime.datetime(2012, 3, 1))
        self.assertEquals(data[3], b)

    def test_generate_series_integer(self):
        series = GenerateSeries(5, 10),
        data = list(self.store.using(series).find(Field('generate_series', 'generate_series')))
        self.assertEquals(len(data), 6)

        self.assertEquals(data, [5, 6, 7, 8, 9, 10])

    def test_case(self):
        # Ordinary case
        series = GenerateSeries(0, 5)
        case = Case(condition=Field('generate_series', 'generate_series') <= 3,
                    result=0, else_=1)
        data = list(self.store.using(series).find(case))
        self.assertEquals(data, [0, 0, 0, 0, 1, 1])

        # else_ is None
        case = Case(condition=Field('generate_series', 'generate_series') <= 3,
                    result=Field('generate_series', 'generate_series'),
                    else_=None)
        data = list(self.store.using(series).find(case))
        self.assertEquals(data, [0, 1, 2, 3, None, None])

        # else_ is a False equivalent value
        case = Case(condition=Field('generate_series', 'generate_series') <= 3,
                    result=Field('generate_series', 'generate_series'), else_=0)
        data = list(self.store.using(series).find(case))
        self.assertEquals(data, [0, 1, 2, 3, 0, 0])

        # else_ is False
        case = Case(condition=Field('generate_series', 'generate_series') != 1,
                    result=True, else_=False)
        data = list(self.store.using(series).find(case))
        self.assertEquals(data, [True, False, True, True, True, True])

        # result is None
        case = Case(condition=Field('generate_series', 'generate_series') != 1,
                    result=None, else_=False)
        data = list(self.store.using(series).find(case))
        self.assertEquals(data, [None, False, None, None, None, None])
