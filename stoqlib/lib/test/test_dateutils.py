# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
import unittest

from stoqlib.lib.dateutils import (create_date_interval,
                                   get_month_intervals_for_year,
                                   INTERVALTYPE_DAY,
                                   INTERVALTYPE_WEEK,
                                   INTERVALTYPE_MONTH,
                                   INTERVALTYPE_BIWEEK,
                                   INTERVALTYPE_QUARTER,
                                   INTERVALTYPE_YEAR)


class DateUtilTest(unittest.TestCase):

    def test_create_date_interval_daily(self):
        dates = create_date_interval(INTERVALTYPE_DAY,
                                     datetime.date(2011, 1, 1),
                                     datetime.date(2011, 12, 31))
        self.assertEquals(dates.count(), 365)

    def test_create_date_interval_month1(self):
        dates = create_date_interval(INTERVALTYPE_MONTH,
                                     datetime.date(2011, 1, 1),
                                     datetime.date(2011, 12, 31))
        self.assertEquals(dates.count(), 12)
        for i, day in enumerate([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]):
            self.assertEquals(dates[i],
                              datetime.datetime(2011, i + 1, day))

    def test_create_date_interval_month5(self):
        dates = create_date_interval(INTERVALTYPE_MONTH,
                                     datetime.date(2011, 1, 5),
                                     datetime.date(2011, 12, 31))
        self.assertEquals(dates.count(), 12)

        for i, day in enumerate([5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]):
            self.assertEquals(dates[i],
                              datetime.datetime(2011, i + 1, day))

    def test_create_date_interval_month29(self):
        dates = create_date_interval(INTERVALTYPE_MONTH,
                                     datetime.date(2011, 1, 29),
                                     datetime.date(2011, 12, 31))
        self.assertEquals(dates.count(), 12)

        for i, day in enumerate([29, 28, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29]):
            self.assertEquals(dates[i],
                              datetime.datetime(2011, i + 1, day))

    def test_create_date_interval_month30(self):
        dates = create_date_interval(INTERVALTYPE_MONTH,
                                     datetime.date(2011, 1, 30),
                                     datetime.date(2011, 12, 31))
        self.assertEquals(dates.count(), 12)

        for i, day in enumerate([30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]):
            self.assertEquals(dates[i],
                              datetime.datetime(2011, i + 1, day))

    def test_create_date_interval_month31(self):
        dates = create_date_interval(INTERVALTYPE_MONTH,
                                     datetime.date(2011, 1, 31),
                                     datetime.date(2011, 12, 31))
        self.assertEquals(dates.count(), 12)

        for i, day in enumerate([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]):
            self.assertEquals(dates[i],
                              datetime.datetime(2011, i + 1, day))

    def test_create_date_interval_weekly(self):
        dates = create_date_interval(INTERVALTYPE_WEEK,
                                     datetime.date(2012, 1, 1),
                                     datetime.date(2012, 12, 31))
        self.assertEquals(dates.count(), 53)
        self.assertEquals(dates[0], datetime.datetime(2012, 1, 1))
        self.assertEquals(dates[52], datetime.datetime(2012, 12, 30))
        for date in dates:
            self.assertEquals(date.weekday(), dates[0].weekday())

    def test_create_date_interval_bi_weekly(self):
        dates = create_date_interval(INTERVALTYPE_BIWEEK,
                                     datetime.date(2012, 1, 1),
                                     datetime.date(2012, 12, 31))
        self.assertEquals(dates.count(), 27)
        self.assertEquals(dates[0], datetime.datetime(2012, 1, 1))
        self.assertEquals(dates[26], datetime.datetime(2012, 12, 30))

    def test_create_repeat_quarterly(self):
        dates = create_date_interval(INTERVALTYPE_QUARTER,
                                     datetime.date(2012, 1, 1),
                                     datetime.date(2012, 12, 31))
        self.assertEquals(dates.count(), 4)
        self.assertEquals(dates[0], datetime.datetime(2012, 1, 1))
        self.assertEquals(dates[1], datetime.datetime(2012, 4, 1))
        self.assertEquals(dates[2], datetime.datetime(2012, 7, 1))
        self.assertEquals(dates[3], datetime.datetime(2012, 10, 1))

    def test_create_repeat_yearly(self):
        dates = create_date_interval(INTERVALTYPE_YEAR,
                                     datetime.date(2012, 1, 1),
                                     datetime.date(2015, 12, 31))
        self.assertEquals(dates.count(), 4)
        self.assertEquals(dates[0], datetime.datetime(2012, 1, 1))
        self.assertEquals(dates[1], datetime.datetime(2013, 1, 1))
        self.assertEquals(dates[2], datetime.datetime(2014, 1, 1))
        self.assertEquals(dates[3], datetime.datetime(2015, 1, 1))

    def test_create_date_interval_none_invalid_interval_type(self):
        self.assertRaises(AssertionError, create_date_interval, 99,
                          datetime.date(2012, 1, 1),
                          datetime.date(2012, 1, 1))

    def test_create_date_interval_count_day(self):
        dates = create_date_interval(interval_type=INTERVALTYPE_DAY,
                                     count=5,
                                     interval=1,
                                     start_date=datetime.date(2012, 1, 1))
        self.assertEquals(dates.count(), 5)
        self.assertEquals(dates[0], datetime.datetime(2012, 1, 1))
        self.assertEquals(dates[1], datetime.datetime(2012, 1, 2))
        self.assertEquals(dates[2], datetime.datetime(2012, 1, 3))
        self.assertEquals(dates[3], datetime.datetime(2012, 1, 4))
        self.assertEquals(dates[4], datetime.datetime(2012, 1, 5))

        dates = create_date_interval(interval_type=INTERVALTYPE_DAY,
                                     count=5,
                                     interval=1,
                                     start_date=datetime.date(2012, 1, 30))
        self.assertEquals(dates.count(), 5)
        self.assertEquals(dates[0], datetime.datetime(2012, 1, 30))
        self.assertEquals(dates[1], datetime.datetime(2012, 1, 31))
        self.assertEquals(dates[2], datetime.datetime(2012, 2, 1))
        self.assertEquals(dates[3], datetime.datetime(2012, 2, 2))
        self.assertEquals(dates[4], datetime.datetime(2012, 2, 3))

    def test_create_date_interval_count_week(self):
        dates = create_date_interval(interval_type=INTERVALTYPE_WEEK,
                                     count=5,
                                     interval=1,
                                     start_date=datetime.date(2012, 1, 1))
        self.assertEquals(dates.count(), 5)
        self.assertEquals(dates[0], datetime.datetime(2012, 1, 1))
        self.assertEquals(dates[1], datetime.datetime(2012, 1, 8))
        self.assertEquals(dates[2], datetime.datetime(2012, 1, 15))
        self.assertEquals(dates[3], datetime.datetime(2012, 1, 22))
        self.assertEquals(dates[4], datetime.datetime(2012, 1, 29))

        dates = create_date_interval(interval_type=INTERVALTYPE_WEEK,
                                     count=5,
                                     interval=1,
                                     start_date=datetime.date(2012, 1, 30))
        self.assertEquals(dates.count(), 5)
        self.assertEquals(dates[0], datetime.datetime(2012, 1, 30))
        self.assertEquals(dates[1], datetime.datetime(2012, 2, 6))
        self.assertEquals(dates[2], datetime.datetime(2012, 2, 13))
        self.assertEquals(dates[3], datetime.datetime(2012, 2, 20))
        self.assertEquals(dates[4], datetime.datetime(2012, 2, 27))

    def test_create_date_interval_count_month(self):
        dates = create_date_interval(interval_type=INTERVALTYPE_MONTH,
                                     count=5,
                                     interval=1,
                                     start_date=datetime.date(2012, 1, 1))
        self.assertEquals(dates.count(), 5)
        self.assertEquals(dates[0], datetime.datetime(2012, 1, 1))
        self.assertEquals(dates[1], datetime.datetime(2012, 2, 1))
        self.assertEquals(dates[2], datetime.datetime(2012, 3, 1))
        self.assertEquals(dates[3], datetime.datetime(2012, 4, 1))
        self.assertEquals(dates[4], datetime.datetime(2012, 5, 1))

        dates = create_date_interval(interval_type=INTERVALTYPE_MONTH,
                                     count=5,
                                     interval=1,
                                     start_date=datetime.date(2012, 1, 30))
        self.assertEquals(dates.count(), 5)
        self.assertEquals(dates[0], datetime.datetime(2012, 1, 30))
        self.assertEquals(dates[1], datetime.datetime(2012, 2, 29))  # leap day
        self.assertEquals(dates[2], datetime.datetime(2012, 3, 30))
        self.assertEquals(dates[3], datetime.datetime(2012, 4, 30))
        self.assertEquals(dates[4], datetime.datetime(2012, 5, 30))

    def test_create_date_interval_count_year(self):
        dates = create_date_interval(interval_type=INTERVALTYPE_YEAR,
                                     count=5,
                                     interval=1,
                                     start_date=datetime.date(2012, 1, 1))
        self.assertEquals(dates.count(), 5)
        self.assertEquals(dates[0], datetime.datetime(2012, 1, 1))
        self.assertEquals(dates[1], datetime.datetime(2013, 1, 1))
        self.assertEquals(dates[2], datetime.datetime(2014, 1, 1))
        self.assertEquals(dates[3], datetime.datetime(2015, 1, 1))
        self.assertEquals(dates[4], datetime.datetime(2016, 1, 1))

    def test_get_month_interval_for_year(self):
        months = list(get_month_intervals_for_year(2012))
        self.assertTrue(len(months), 12)
        self.assertTrue(months[0], (datetime.datetime(2012, 1, 1),
                                    datetime.datetime(2012, 1, 31)))
        self.assertTrue(months[11], (datetime.datetime(2012, 12, 1),
                                     datetime.datetime(2012, 12, 31)))
