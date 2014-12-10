# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Search options for filters"""

import datetime

from dateutil.relativedelta import relativedelta

from stoqlib.database.queryexecuter import StringQueryState, NumberQueryState
from stoqlib.lib.defaults import get_weekday_start
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


#
# Date Search Options
#

class DateSearchOption(object):
    """
    Base class for Date search options
    A date search option is an interval of dates
    :cvar name: name of the search option
    """
    name = None

    def get_today_date(self):
        return datetime.date.today()

    def get_interval(self):
        """
        Get start and end date.
        :returns: start date, end date
        :rtype: datetime.date tuple
        """


class Any(DateSearchOption):
    name = _('Any')

    def get_interval(self):
        return None, None


class Yesterday(DateSearchOption):
    name = _('Yesterday')

    def get_interval(self):
        yesterday = self.get_today_date() - datetime.timedelta(days=1)
        return yesterday, yesterday


class Today(DateSearchOption):
    name = _('Today')

    def get_interval(self):
        today = self.get_today_date()
        return today, today


class LastWeek(DateSearchOption):
    name = _('Last week')

    def get_interval(self):
        today = self.get_today_date()
        weekday = get_weekday_start()

        start = today + relativedelta(weeks=-1, weekday=weekday(-1))
        end = start + relativedelta(days=+6)
        return start, end


class ThisWeek(DateSearchOption):
    name = _('This week')

    def get_interval(self):
        today = self.get_today_date()
        weekday = get_weekday_start()

        start = today + relativedelta(weekday=weekday(-1))
        end = start + relativedelta(days=+6)
        return start, end


class NextWeek(DateSearchOption):
    name = _('Next week')

    def get_interval(self):
        today = self.get_today_date()
        weekday = get_weekday_start()
        start = today + relativedelta(days=+1, weekday=weekday(+1))
        end = start + relativedelta(days=+6)
        return start, end


class LastMonth(DateSearchOption):
    name = _('Last month')

    def get_interval(self):
        today = self.get_today_date()
        start = today + relativedelta(months=-1, day=1)
        end = today + relativedelta(months=-1, day=31)
        return start, end


class ThisMonth(DateSearchOption):
    name = _('This month')

    def get_interval(self):
        today = self.get_today_date()
        start = today + relativedelta(day=1)
        end = today + relativedelta(day=31)
        return start, end


class NextMonth(DateSearchOption):
    name = _('Next month')

    def get_interval(self):
        today = self.get_today_date()
        start = today + relativedelta(months=+1, day=1)
        end = today + relativedelta(months=+1, day=31)
        return start, end


class FixedIntervalSearchOption(DateSearchOption):
    start = None
    end = None

    def get_interval(self):
        return self.start, self.end


class FixedDateSearchOption(DateSearchOption):
    date = None

    def get_interval(self):
        return self.date, self.date


#
#   Number Search Options
#

class NumberSearchOption(object):
    """
    Base class for Number search options
    A number search option is an interval of numbers
    :cvar name: name of the search option
    :cvar numbers: how many numbers must the user input: 0, 1 or 2
    """
    name = None
    numbers = 0

    def get_interval(self, start, end):
        """
        Get start and end interval.
        :returns: start, end
        """


class Between(NumberSearchOption):
    name = _('Between')
    numbers = 2

    def get_interval(self, start, end):
        return (start, end)


class EqualsTo(NumberSearchOption):
    name = _('Equals to')
    numbers = 1

    def get_interval(self, start, end):
        return (start, start)


class GreaterThan(NumberSearchOption):
    name = _('Greater or Equal')
    numbers = 1

    def get_interval(self, start, end):
        return (start, None)


class LowerThan(NumberSearchOption):
    name = _('Lower or Equal')
    numbers = 1

    def get_interval(self, start, end):
        return (None, start)


#
#   String Search Options
#

class StringSearchOption(object):
    pass


class IdenticalTo(StringSearchOption):
    name = _('Identical to')
    mode = StringQueryState.IDENTICAL_TO


class ContainsExactly(StringSearchOption):
    name = _('Contains Exactly')
    mode = StringQueryState.CONTAINS_EXACTLY


class ContainsAll(StringSearchOption):
    name = _('Contains All Words')
    mode = StringQueryState.CONTAINS_ALL


class DoesNotContain(StringSearchOption):
    name = _('Does Not Contain')
    mode = StringQueryState.NOT_CONTAINS


#
#   Combo Search Options
#

class ComboSearchOption(object):
    pass


class ComboEquals(ComboSearchOption):
    name = _('Equals to')
    mode = NumberQueryState.EQUALS


class ComboDifferent(ComboSearchOption):
    name = _('Different from')
    mode = NumberQueryState.DIFFERENT
