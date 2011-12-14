# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2011 Async Open Source
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Date constants"""

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


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
