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
"""Utilities for working with dates"""

import collections
import datetime

from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
(INTERVALTYPE_DAY,
 INTERVALTYPE_WEEK,
 INTERVALTYPE_MONTH,
 INTERVALTYPE_YEAR,
 INTERVALTYPE_BIWEEK,
 INTERVALTYPE_QUARTER,
 INTERVALTYPE_YEAR) = range(7)

_Interval = collections.namedtuple(
    'Interval', 'multiple singular plural adverb constant')

_interval_types = [
    _Interval(1, _('day'), _('days'), _('Daily'), INTERVALTYPE_DAY),
    _Interval(1, _('week'), _('weeks'), _('Weekly'), INTERVALTYPE_WEEK),
    _Interval(2, _('week'), _('weeks'), _('Biweekly'), INTERVALTYPE_BIWEEK),
    _Interval(1, _('month'), _('months'), _('Monthly'), INTERVALTYPE_MONTH),
    _Interval(4, _('month'), _('months'), _('Quarterly'), INTERVALTYPE_QUARTER),
    _Interval(1, _('year'), _('years'), _('Yearly'), INTERVALTYPE_YEAR),
]


def localnow():
    """Get the current date according to the local timezone.
    This is relative to the clock on the computer where Stoq is run.

    :rtype: datetime.datetime object
    :returns: right now according to the current locale
    """
    # FIXME: When we can use TIMEZONE WITH TIMESTAMP in PostgreSQL
    #        this should set the timezone.
    return datetime.datetime.now()


def localtoday():
    """Get the beginning of the current date according to the local timezone.
    This is relative to the clock on the computer where Stoq is run.

    :rtype: datetime.datetime object
    :returns: today according to the current locale
    """
    return localnow().replace(hour=0,
                              minute=0,
                              second=0,
                              microsecond=0)


def localdate(year, month, day):
    """Get a date according to the local timezone.
    This will return a date at midnight for the current locale.
    This is relative to the clock on the computer where Stoq is run.

    :param int year: the year in four digits
    :param int month: the month (1-12)
    :param int day: the day (1-31)
    :rtype: datetime.datetime object
    :returns: a date according to the current locale
    """
    return localdatetime(year, month, day)


def localdatetime(year, month, day, hour=0, minute=0, second=0,
                  microsecond=0):
    """Get a datetime according to the local timezone.
    This will return a date at midnight for the current locale.
    This is relative to the clock on the computer where Stoq is run.

    :param int year: the year in four digits
    :param int month: the month (1-12)
    :param int day: the day (1-31)
    :param int hour: the hour (0-23)
    :param int minute: the minute (0-59)
    :param int second: the second (0-59)
    :param int microsecond: the microsecond (1-99999)
    :rtype: datetime.datetime object
    :returns: a date according to the current locale
    """
    # FIXME: When we can use TIMEZONE WITH TIMESTAMP in PostgreSQL
    #        this should set the timezone.
    return datetime.datetime(year=year, day=day, month=month,
                             hour=hour, minute=minute, second=second,
                             microsecond=microsecond)


def get_interval_type_items(with_multiples=False,
                            plural=False,
                            adverb=False):
    """Get a list of items suitable for putting into a combo.
    You can get three variants, singular, plural or adverb depending
    on how you want to display it. You can skip multiples if you plan
    to use them in conjuction with a spinbutton

    :param with_multiples: if multiples such as biweekly and quarterly should
      be included
    :param plural: if the plural variant should be used
    :param adverb: if the adverbial form should be used
    :returns: a list of tuples (labels, interval_type)
    """
    labels = []
    for interval in _interval_types:
        if not with_multiples and interval.multiple > 1:
            continue
        if adverb:
            label = interval.adverb
        elif plural:
            label = interval.plural
        else:
            label = interval.singular
        labels.append((label, interval.constant))
    return labels


def get_month_names():
    return [_('January'),
            _('February'),
            _('March'),
            _('April'),
            _('May'),
            _('June'),
            _('July'),
            _('August'),
            _('September'),
            _('October'),
            _('November'),
            _('December')]


def get_short_month_names():
    return [_('Jan'),
            _('Feb'),
            _('Mar'),
            _('Apr'),
            _('May'),
            _('Jun'),
            _('Jul'),
            _('Aug'),
            _('Sep'),
            _('Oct'),
            _('Nov'),
            _('Dec')]


def get_day_names():
    return [_('Sunday'),
            _('Monday'),
            _('Tuesday'),
            _('Wednesday'),
            _('Thursday'),
            _('Friday'),
            _('Saturday')]


def get_short_day_names():
    return [_('Sun'),
            _('Mon'),
            _('Tue'),
            _('Wed'),
            _('Thu'),
            _('Fri'),
            _('Sat')]


def create_date_interval(interval_type,
                         start_date=None,
                         end_date=None,
                         interval=None,
                         count=None):
    """Generate a bunch of dates given a set of parameters.
    There are two ways of using this, either as:

      * interval_type, interval, count, start_date

    or:

      * interval_type, start_date, end_date


    :param interval_type: one of the INTERVALTYPE_* above
    :param intervals: interval between the dates
    :param count: number of items to create
    :param start_date: start :class:`date <datetime.date>`
    :param end_date: end :class:`date <datetime.date>`
    :returns: a :class:`datetime.rrule.rrule` object
    """
    if ((not interval and
         not count and
         not start_date) and
        (not start_date and
         not end_date)):
        raise TypeError("Needs interval/count/end date or start/end date")
    if interval and (not start_date and not count):
        raise TypeError("interval needs start_date/count")
    if interval and end_date:
        raise TypeError("Can't specify both interval and end date")

    bymonthday = None
    bysetpos = None
    if interval_type == INTERVALTYPE_DAY:
        freq = DAILY
        _interval = 1
    elif interval_type == INTERVALTYPE_WEEK:
        freq = WEEKLY
        _interval = 1
    elif interval_type == INTERVALTYPE_BIWEEK:
        freq = WEEKLY
        _interval = 2
    elif interval_type == INTERVALTYPE_MONTH:
        # This really means: last day of month, it'll never
        # cross month boundaries even if there are less than
        # 31 days.
        bysetpos = 1
        bymonthday = (start_date.day, -1)
        freq = MONTHLY
        _interval = 1
    elif interval_type == INTERVALTYPE_QUARTER:
        freq = MONTHLY
        _interval = 3
    elif interval_type == INTERVALTYPE_YEAR:
        freq = YEARLY
        _interval = 1
    else:
        raise AssertionError(interval_type)

    if not interval:
        interval = _interval

    return rrule(dtstart=start_date,
                 until=end_date,
                 freq=freq,
                 interval=interval,
                 count=count,
                 bymonthday=bymonthday,
                 bysetpos=bysetpos)


def interval_type_as_relativedelta(interval_type):
    """
    Gets a interval_type as a relativedelta

    :returns: a relativedelta
    """
    if interval_type == INTERVALTYPE_DAY:
        return relativedelta(days=1)
    elif interval_type == INTERVALTYPE_WEEK:
        return relativedelta(weeks=1)
    elif interval_type == INTERVALTYPE_BIWEEK:
        return relativedelta(weeks=2)
    elif interval_type == INTERVALTYPE_MONTH:
        return relativedelta(months=1)
    elif interval_type == INTERVALTYPE_QUARTER:
        return relativedelta(months=3)
    elif interval_type == INTERVALTYPE_YEAR:
        return relativedelta(years=1)
    else:
        raise AssertionError(interval_type)


def get_month_intervals_for_year(year):
    """Returns a list of tuples with first and last day of a month"""
    months = iter(
        rrule(MONTHLY,
              count=24,  # 2 per year, 12 months
              bymonthday=(1, -1),
              dtstart=datetime.datetime(year, 1, 1)))

    while True:
        try:
            yield months.next(), months.next()
        except StopIteration:
            break


def _df(seconds, denominator, past, text_future, text_past):
    if past:
        return text_past % ((seconds + denominator / 2) / denominator, )
    else:
        return text_future % ((seconds + denominator / 2) / denominator, )


# pretty_date() is:
# __author__ = "S Anand (sanand@s-anand.net)"
# __copyright__ = "Copyright 2010, S Anand"
# __license__ = "WTFPL"

def pretty_date(time=False, asdays=False):
    '''Returns a pretty formatted date.
    Inputs:
        time is a datetime object or an int timestamp
        asdays is True if you only want to measure days, not seconds
    '''

    now = datetime.datetime.now()
    if type(time) is int:
        time = datetime.datetime.fromtimestamp(time)
    elif not time:
        time = now

    if time > now:
        past = False
        diff = time - now
    else:
        past = True
        diff = now - time

    seconds = diff.seconds
    days = diff.days

    if days == 0 and not asdays:
        if seconds < 10:
            return _('now')
        elif seconds < 60:
            return _df(seconds, 1, past,
                       _('in %d seconds'),
                       _('%d seconds ago'))
        elif seconds < 120:
            return _('a minute ago') if past else _('in a minute')
        elif seconds < 3600:
            return _df(seconds, 60, past,
                       _('in %d minutes'),
                       _('%d minutes ago'))
        elif seconds < 7200:
            return _('an hour ago') if past else _('in an hour')
        else:
            return _df(seconds, 3600, past,
                       _('in %d hours'),
                       _('%d hours ago'))
    else:
        if days == 0:
            return _('today')
        elif days == 1:
            return _('yesterday') if past else _('tomorrow')
        elif days == 2:
            return _('day before') if past else _('day after')
        elif days < 7:
            return _df(days, 1, past,
                       _('in %d days'),
                       _('%d days ago'))
        elif days < 14:
            return _('last week') if past else _('next week')
        elif days < 31:
            return _df(days, 7, past,
                       _('in %d weeks'),
                       _('%d weeks ago'))
        elif days < 61:
            return _('last month') if past else _('next month')
        elif days < 365:
            return _df(days, 30, past,
                       _('in %d months'),
                       _('%d months ago'))
        elif days < 730:
            return _('last year') if past else _('next year')
        else:
            return _df(days, 365, past,
                       _('in %d years'),
                       _('%d years ago'))
