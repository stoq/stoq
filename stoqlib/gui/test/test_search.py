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

from dateutil import relativedelta
from dateutil.relativedelta import SU, MO, SA, relativedelta as delta

from twisted.trial import unittest

from stoqlib.gui.base.search import (ThisWeek, LastWeek, NextWeek, ThisMonth,
                                     LastMonth, NextMonth)
from stoqlib.lib.defaults import get_weekday_start


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

    # Tests disable because they cause segmentation fault in hudson
    def DISABLED_testThisWeek(self):
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

    def DISABLED_testLastWeek(self):
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

    def DISABLED_testNextWeek(self):
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

    def DISABLED_testThisMonth(self):
        option = ThisMonth()
        for loc in self._get_locales():
            self._set_locale(loc)
            for month_day in [datetime.date(2007, 1, 1),
                              datetime.date(2007, 1, 15),
                              datetime.date(2007, 1, 31)]:
                option.get_today_date = lambda: month_day

                self.assertEqual(option.get_interval(),
                                 self._get_month_interval(month_day))

    def DISABLED_testLastMonth(self):
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
