# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2009 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

__author__ = "S Anand (sanand@s-anand.net)"
__copyright__ = "Copyright 2010, S Anand"
__license__ = "WTFPL"

import datetime

from stoqlib.lib.translation import stoqlib_gettext
_ = stoqlib_gettext


def _df(seconds, denominator=1, text='', past=True):
    if past:
        # Translators: 15 [days|weeks|months|years] ago
        return _('%s %s ago') % ((seconds + denominator/2)/denominator, text)
    else:
        # Translators: in 15 [days|weeks|months|years]
        return _('in %s %s') % ((seconds + denominator/2)/denominator, text)


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
            return _df(seconds, 1, _('seconds'), past)
        elif seconds < 120:
            return past and _('a minute ago') or _('in a minute')
        elif seconds < 3600:
            return _df(seconds, 60, _('minutes'), past)
        elif seconds < 7200:
            return past and _('an hour ago') or _('in an hour')
        else:
            return _df(seconds, 3600, _('hours'), past)
    else:
        if days   == 0:
            return _('today')
        elif days   == 1:
            return past and _('yesterday') or _('tomorrow')
        elif days   == 2:
            return past and _('day before') or _('day after')
        elif days    < 7:
            return _df(days, 1, _('days'), past)
        elif days    < 14:
            return past and _('last week') or _('next week')
        elif days    < 31:
            return _df(days, 7, _('weeks'), past)
        elif days    < 61:
            return past and _('last month') or _('next month')
        elif days    < 365:
            return _df(days, 30, _('months'), past)
        elif days    < 730:
            return past and _('last year') or _('next year')
        else:
            return _df(days, 365, _('years'), past)
