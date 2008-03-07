# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##

"""
Events used in the domain code
"""

from stoqlib.lib.event import Event


#
# Sale events
#

class SaleConfirmEvent(Event):
    """
    This event is emitted when a sale is confirmed

    @param sale: the confirmed sale
    """


#
# Till events
#

class TillOpenEvent(Event):
    """
    This event is emitted when a till is opened
    @param till: the opened till
    """


class TillCloseEvent(Event):
    """
    This event is emitted when a till is closed
    @param till: the closed till
    @param previous_day: if the till wasn't closed previously
    """


class TillAddCashEvent(Event):
    """
    This event is emitted when cash is added to a till
    @param till: the closed till
    @param value: amount added to the till
    """


class TillRemoveCashEvent(Event):
    """
    This event is emitted when cash is removed from a till
    @param till: the closed till
    @param value: amount remove from the till
    """


class TillAddTillEntryEvent(Event):
    """
    This event is emitted when:

    cash is added to a till;
    cash is removed from a till;
    @param till_entry: TillEntry object
    @param conn: database connection
    """

