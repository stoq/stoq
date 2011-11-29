# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

from kiwi.argcheck import argcheck
from zope.interface import implements

from stoqlib.database.orm import (AND, UnicodeCol, IntCol, ForeignKey,
                                  BoolCol, ILIKE)
from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CityLocation(Domain):
    """Base class to store the locations. Used to store a person's address
    or birth location.
    """

    country = UnicodeCol(default=u"")
    city = UnicodeCol(default=u"")
    state = UnicodeCol(default=u"")

    @classmethod
    @argcheck(StoqlibTransaction)
    def get_default(cls, trans):
        city = sysparam(trans).CITY_SUGGESTED
        state = sysparam(trans).STATE_SUGGESTED
        country = sysparam(trans).COUNTRY_SUGGESTED

        location = CityLocation.selectOneBy(city=city, state=state,
                                            country=country,
                                            connection=trans)

        # FIXME: Move this to database initialization ?
        if location is None:
            location = CityLocation(city=city, state=state, country=country,
                                    connection=trans)
        return location

    def is_valid_model(self):
        return bool(self.country and self.city and self.state)

    @classmethod
    @argcheck(StoqlibTransaction, basestring, basestring, basestring)
    def get_or_create(cls, trans, city, state, country):
        """
        Returns a CityLocation. If it does not exist, create a new
        one and return it.
        @param trans: a database transaction
        @param city: city
        @param state: state
        @param country: country
        @returns: a L{CityLocation} or None
        """
        location = CityLocation.selectOne(
            AND(ILIKE(CityLocation.q.city, city),
                ILIKE(CityLocation.q.state, state),
                ILIKE(CityLocation.q.country, country)),
            connection=trans)
        if not location:
            location = CityLocation(
                city=city,
                state=state,
                country=country,
                connection=trans)
        return location


class Address(Domain):
    """Class to store person's addresses.

    B{Important Attributes}:
       - I{is_main_address}: defines if this object stores information
                             for the main address
    """

    implements(IDescribable)

    street = UnicodeCol(default='')
    streetnumber = IntCol(default=None)
    district = UnicodeCol(default='')
    postal_code = UnicodeCol(default='')
    complement = UnicodeCol(default='')
    is_main_address = BoolCol(default=False)
    person = ForeignKey('Person')
    city_location = ForeignKey('CityLocation')

    def is_valid_model(self):
        return (self.street and self.district and
                self.city_location.is_valid_model())

    def get_city(self):
        return self.city_location.city

    def get_country(self):
        return self.city_location.country

    def get_state(self):
        return self.city_location.state

    def get_postal_code_number(self):
        """Returns the postal code without any non-numeric characters
        @returns: the postal code as a number
        @rtype: integer
        """
        if not self.postal_code:
            return 0
        return int(''.join([c for c in self.postal_code
                                  if c in '1234567890']))

    def get_address_string(self):
        if self.street and self.streetnumber and self.district:
            return u'%s %s, %s' % (self.street, self.streetnumber,
                                   self.district)
        elif self.street and self.district:
            return u'%s %s, %s' % (self.street, _(u'N/A'), self.district)
        elif self.street and self.streetnumber:
            return u'%s %s' % (self.street, self.streetnumber)
        elif self.street:
            return self.street

        return u''

    def get_description(self):
        return self.get_address_string()

    def get_details_string(self):
        """ Returns a string like 'postal_code - city - state'.
        If city or state are missing, return only postal_code; and
        if postal_code is missing, return 'city - state', otherwise,
        return an empty string
        """
        details = []
        if self.postal_code:
            details.append(self.postal_code)
        if self.city_location.city and self.city_location.state:
            details.extend([self.city_location.city,
                            self.city_location.state])
        details = u" - ".join(details)
        return details
