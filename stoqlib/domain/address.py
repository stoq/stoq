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
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##

from kiwi.argcheck import argcheck
from sqlobject.sqlbuilder import AND, func
from sqlobject import (UnicodeCol, IntCol,
                       ForeignKey, BoolCol)
from zope.interface import implements

from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.domain.base import Domain
from stoqlib.lib.parameters import sysparam
from stoqlib.domain.interfaces import IDescribable

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

    def get_similar(self):
        """
        Returns a list of CityLocations which are similar to the current one
        """
        return CityLocation.select(
            AND(func.UPPER(CityLocation.q.city) == self.city.upper(),
                func.UPPER(CityLocation.q.state) == self.state.upper(),
                func.UPPER(CityLocation.q.country) == self.country.upper(),
                CityLocation.q.id != self.id),
            connection=self.get_connection())

class Address(Domain):
    """Class to store person's addresses.

    B{Important Attributes}:
       - I{is_main_address}: defines if this object stores information
                             for the main address
    """

    implements(IDescribable)

    street = UnicodeCol(default='')
    number = IntCol(default=None)
    district = UnicodeCol(default='')
    postal_code = UnicodeCol(default='')
    complement = UnicodeCol(default='')
    is_main_address = BoolCol(default=False)
    person = ForeignKey('Person')
    city_location = ForeignKey('CityLocation')

    def is_valid_model(self):
        return (self.street and self.number and self.district
                and self.city_location.is_valid_model())

    def ensure_address(self):
        """
        Verify that the current CityLocation instance is unique.
        If it's not unique replace it with the one which is similar/identical
        """
        similar = self.city_location.get_similar()
        if similar:
            location = self.city_location
            self.city_location = similar.getOne()
            CityLocation.delete(location.id, connection=self.get_connection())

    def get_city(self):
        return self.city_location.city

    def get_country(self):
        return self.city_location.country

    def get_state(self):
        return self.city_location.state

    def get_postal_code_number(self):
        """
        Returns the postal code without any non-numeric characters
        @returns: the postal code as a number
        @rtype: integer
        """
        return int(''.join([c for c in self.postal_code
                                  if c in '1234567890']))

    def get_address_string(self):
        if self.street and self.number and self.district:
            return u'%s %s, %s' % (self.street, self.number,
                                   self.district)
        elif self.street and self.number:
            return u'%s %s' % (self.street, self.number)
        elif self.street:
            return self.street

        return u''

    def get_description(self):
        return self.get_address_string()
