# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
import locale
import unittest

from dateutil import relativedelta
from dateutil.relativedelta import SU, MO, SA, relativedelta as delta
from nose.exc import SkipTest

from kiwi.ui.objectlist import SearchColumn
from kiwi.ui.search import (StringSearchFilter, DateSearchFilter,
                            ComboSearchFilter, NumberSearchFilter)

from stoqlib.api import api
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.gui.base.search import SearchDialog
from stoqlib.gui.base.search import (ThisWeek, LastWeek, NextWeek, ThisMonth,
                                     LastMonth, NextMonth)
from stoqlib.lib.defaults import get_weekday_start
from stoqlib.lib.introspection import get_all_classes


class TestDateOptions(unittest.TestCase):

    def tearDown(self):
        self._set_locale("")

    def _get_week_interval(self, today):
        weekday = get_weekday_start()
        start = today + delta(weekday=weekday(-1))
        end = start + delta(days=+6)
        return start, end

    def _get_month_interval(self, today):
        start = today + delta(day=1)
        end = start + delta(day=31)
        return start, end

    def _get_locales(self):
        # en_US: week starts on sunday
        # es_ES: week starts on monday
        return ["en_US", "es_ES"]

    def _starts_on_sunday(self, loc):
        return loc == "en_US"

    def _set_locale(self, loc):
        try:
            locale.setlocale(locale.LC_ALL, loc)
        except locale.Error:
            # Some locales could not be available on user's machine, leading
            # him to a false positive broke test, so skip it, informing the
            # problem.
            raise unittest.SkipTest("Locale %s not available" % (loc, ))

    def _testWeekday(self, loc, interval):
        if self._starts_on_sunday(loc):
            self.assertEqual(
                relativedelta.weekday(interval[0].weekday()), SU)
            self.assertEqual(
                relativedelta.weekday(interval[1].weekday()), SA)
        else:
            self.assertEqual(
                relativedelta.weekday(interval[0].weekday()), MO)
            self.assertEqual(
                relativedelta.weekday(interval[1].weekday()), SU)

    def testThisWeek(self):
        raise SkipTest("Segmentation fault in jenkins")
        option = ThisWeek()
        for loc in self._get_locales():
            self._set_locale(loc)
            # starting in 2008/01/01, wednesday
            for i in range(1, 8):
                get_today_date = lambda: datetime.date(2008, 1, i)
                option.get_today_date = get_today_date
                self.assertEqual(option.get_interval(),
                                 self._get_week_interval(get_today_date()))
                self._testWeekday(loc, option.get_interval())

    def testLastWeek(self):
        raise SkipTest("Segmentation fault in jenkins")
        option = LastWeek()
        for loc in self._get_locales():
            self._set_locale(loc)
            # starting in 2008/01/01, wednesday
            for i in range(1, 8):
                get_today_date = lambda: datetime.date(2008, 1, i)
                option.get_today_date = get_today_date

                last_week_day = get_today_date() + delta(weeks=-1)
                self.assertEqual(option.get_interval(),
                                 self._get_week_interval(last_week_day))
                self._testWeekday(loc, option.get_interval())

    def testNextWeek(self):
        raise SkipTest("Segmentation fault in jenkins")
        option = NextWeek()
        for loc in self._get_locales():
            self._set_locale(loc)
            # starting in 2008/01/01, wednesday
            for i in range(1, 8):
                get_today_date = lambda: datetime.date(2008, 1, i)
                option.get_today_date = get_today_date

                next_week_day = get_today_date() + delta(weeks=+1)
                self.assertEqual(option.get_interval(),
                                 self._get_week_interval(next_week_day))
                self._testWeekday(loc, option.get_interval())

    def testThisMonth(self):
        raise SkipTest("Segmentation fault in jenkins")
        option = ThisMonth()
        for loc in self._get_locales():
            self._set_locale(loc)
            for month_day in [datetime.date(2007, 1, 1),
                              datetime.date(2007, 1, 15),
                              datetime.date(2007, 1, 31)]:
                option.get_today_date = lambda: month_day

                self.assertEqual(option.get_interval(),
                                 self._get_month_interval(month_day))

    def testLastMonth(self):
        raise SkipTest("Segmentation fault in jenkins")
        option = LastMonth()
        for loc in self._get_locales():
            self._set_locale(loc)
            for month_day in [datetime.date(2007, 1, 1),
                              datetime.date(2007, 1, 15),
                              datetime.date(2007, 1, 31)]:
                option.get_today_date = lambda: month_day

                last_month_day = month_day + delta(months=-1)
                self.assertEqual(option.get_interval(),
                                 self._get_month_interval(last_month_day))

    def testNextMonth(self):
        option = NextMonth()
        for loc in self._get_locales():
            self._set_locale(loc)
            for month_day in [datetime.date(2007, 1, 1),
                              datetime.date(2007, 1, 15),
                              datetime.date(2007, 1, 31)]:
                option.get_today_date = lambda: month_day

                next_month_day = month_day + delta(months=+1)
                self.assertEqual(option.get_interval(),
                                 self._get_month_interval(next_month_day))


class TestSearchGeneric(DomainTest):
    """Generic tests for searches"""

    # Those are base classes for other searches, and should not be instanciated
    ignored_classes = [
        '_SellableSearch',
        '_BaseBillCheckSearch',
        'SearchEditor',
        'BasePersonSearch',
        'AbstractCreditProviderSearch',
    ]

    @classmethod
    def _get_all_searches(cls):
        for klass in get_all_classes('stoqlib/gui'):
            try:
                if klass.__name__ in cls.ignored_classes:
                    continue
                # Exclude Viewable, since we just want to test it's subclasses
                if not issubclass(klass, SearchDialog) or klass is SearchDialog:
                    continue
            except TypeError:
                continue

            yield klass

    def _test_search(self, search_class):
        # XXX: If we use self.trans, the all this tests passes, but the test
        # executed after this will break with
        # storm.exceptions.ClosedError('Connection is closed',)
        trans = api.new_transaction()
        search = search_class(trans)

        # There may be no results in the search, but we only want to check if
        # the query is executed properly
        search.search.refresh()

        # Testing SearchColumns only makes sense if advanced search is enabled
        if not search.search.search.menu:
            return

        columns = search.search.results.get_columns()
        for i in columns:
            if not isinstance(i, SearchColumn):
                continue

            filter = search.search.search.add_filter_by_column(i)

            # Set some value in the filter, so that it acctually is included in
            # the query
            if isinstance(filter, StringSearchFilter):
                filter.set_state('foo')
            elif isinstance(filter, DateSearchFilter):
                filter.set_state(datetime.date(2012, 1, 1),
                                 datetime.date(2012, 10, 10))
            elif isinstance(filter, NumberSearchFilter):
                filter.set_state(1, 3)
            elif isinstance(filter, ComboSearchFilter):
                for key, value in filter.combo.get_model_items().items():
                    if value:
                        filter.set_state(value)
                        break
            search.search.refresh()

            # Remove the filter so it wont affect other searches
            filter.emit('removed')

        trans.close()


for search in TestSearchGeneric._get_all_searches():
    name = 'test' + search.__name__
    func = lambda s, v=search: TestSearchGeneric._test_search(s, v)
    func.__name__ = name
    setattr(TestSearchGeneric, name, func)
    del func
