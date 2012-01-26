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


def _df(seconds, denominator, past, text_future, text_past):
    if past:
        return text_past % ((seconds + denominator / 2) / denominator, )
    else:
        return text_future % ((seconds + denominator / 2) / denominator, )


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
