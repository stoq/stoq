# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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

"""This module contains classes centered around physical addresses.

There are two classes, :class:`Address` and :class:`CityLocation`.

CityLocation contains the city, state and country, Address contains
street, district, postal code and a reference to a |person|.
"""

# pylint: enable=E1101

from storm.expr import And
from storm.references import Reference
from storm.store import AutoReload
from zope.interface import implementer

from stoqlib.database.expr import StoqNormalizeString
from stoqlib.database.orm import ORMObject
from stoqlib.database.properties import UnicodeCol, IntCol, BoolCol, IdCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable
from stoqlib.l10n.l10n import get_l10n_field
from stoqlib.lib.formatters import format_address
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


def _get_equal_clause(table, value):
    # FIXME: Never versions of Psycopg2 treats str as bytes,
    # We should do the same and enable:
    #   from __future__ import unicode_literals
    # and start to convert all APIs to use unicode instead of str.
    if isinstance(value, str):
        value = unicode(value, 'utf-8')
    return (StoqNormalizeString(table) ==
            StoqNormalizeString(value))


# CityLocation inherits from ORMObject to avoid having te_id for a table
# that never is modified after initial import.
class CityLocation(ORMObject):
    """CityLocation is a class that contains the location of a city
    and it's state/country. There are also codes for the city and states.

    The country is expected to be one of the countries returned from
    :func:`stoqlib.lib.countries.get_countries`.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/city_location.html>`__

    .. note:: the city and state codes are currently Brazil specific
              and refers to a unique identifier which is the same as
              NFe (Nota Fiscal Eletronico) requires.

    """

    __storm_table__ = 'city_location'

    id = IntCol(primary=True, default=AutoReload)

    #: the city
    city = UnicodeCol(default=u"")

    # FIXME: state should probably be renamed, as it's an administratal
    #        subdistrict fo a country.
    #: the state
    state = UnicodeCol(default=u"")

    #: the country, iso-3166 localized using iso-codes
    country = UnicodeCol(default=u"")

    #: code of the city
    city_code = IntCol(default=None)

    #: code of the state
    state_code = IntCol(default=None)

    #
    #  Classmethods
    #

    @classmethod
    def get_default(cls, store):
        """Get the default city location according to the database parameters.
        The is usually the same city as main branch.

        :returns: the default city location
        """
        city = sysparam.get_string('CITY_SUGGESTED')
        state = sysparam.get_string('STATE_SUGGESTED')
        country = sysparam.get_string('COUNTRY_SUGGESTED')

        return cls.get_or_create(store, city, state, country)

    @classmethod
    def get_or_create(cls, store, city, state, country):
        """
        Get or create a city location. City locations are created lazily,
        so this is used when registering new addresses.

        :param store: a store
        :param unicode city: a city
        :param unicode state: a state
        :param unicode country: a country
        :returns: the |citylocation| or ``None``
        """

        # FIXME: This should use find().one(). See bug 5146
        location = list(store.find(cls,
                                   And(_get_equal_clause(cls.city, city),
                                       _get_equal_clause(cls.state, state),
                                       _get_equal_clause(cls.country, country))))

        if len(location) == 1:
            return location[0]
        elif len(location) > 1:
            # Choose the best entry from city_location (the one we created)
            for l in location:
                if l.city_code:
                    return l
            # Otherwise, return any object
            return location[0]

        return cls(city=city,
                   state=state,
                   country=country,
                   store=store)

    @classmethod
    def get_cities_by(cls, store, state=None, country=None):
        """Fetch a list of cities given a state and a country.

        :param store: a store
        :param state: state or ``None``
        :param country: country or ``None``
        :returns: a list of cities
        :rtype: string
        """
        clauses = []

        if state:
            clauses.append(_get_equal_clause(cls.state, state))
        if country:
            clauses.append(_get_equal_clause(cls.country, country))

        if clauses:
            results = store.find(cls, And(*clauses))
        else:
            results = store.find(cls)
        return set(result.city for result in results)

    @classmethod
    def exists(cls, store, city, state, country):
        # FIXME: This should use find().one(), but its possible to register
        # duplicate city locations (see bug 5146)
        return bool(store.find(cls, And(
            _get_equal_clause(cls.city, city),
            _get_equal_clause(cls.state, state),
            _get_equal_clause(cls.country, country))).count())

    #
    #  Public API
    #

    def is_valid_model(self):
        city_l10n = get_l10n_field('city', self.country)
        return bool(self.country and self.city and self.state and
                    city_l10n.validate(self.city,
                                       state=self.state, country=self.country))


@implementer(IDescribable)
class Address(Domain):
    """An Address is a class that stores a physical street location
    for a |person|.

    A Person can have many addresses.
    The city, state and country is found in |citylocation|.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/address.html>`__
    """

    __storm_table__ = 'address'

    #: street of the address, something like ``"Wall street"``
    street = UnicodeCol(default=u'')

    #: streetnumber, eg ``100``
    streetnumber = IntCol(default=None)

    #: district, eg ``"Manhattan"``
    district = UnicodeCol(default=u'')

    #: postal code, eg ``"12345-678"``
    postal_code = UnicodeCol(default=u'')

    #: complement, eg ``"apartment 35"``
    complement = UnicodeCol(default=u'')

    #: If this is the primary address for the |person|, this is set
    #: when you register a person for the first time.
    is_main_address = BoolCol(default=False)

    person_id = IdCol()

    #: the |person| who resides at this address
    person = Reference(person_id, 'Person.id')

    city_location_id = IntCol()

    #: the |citylocation| this address is in
    city_location = Reference(city_location_id, 'CityLocation.id')

    #
    # IDescribable
    #

    def get_description(self):
        """See `IDescribable.get_description()`"""
        return self.get_address_string()

    # Public API

    def is_valid_model(self):
        """Verifies if this model is properly filled in,
        that there's a street, district and valid |citylocation| set.

        :returns: ``True`` if this address is filled in.
        """

        # FIXME: This should probably take uiforms into account.
        return (self.street and self.district and
                self.city_location.is_valid_model())

    def get_city(self):
        """Get the city for this address. It's fetched from
        the |citylocation|.

        :returns: the city
        """
        return self.city_location.city

    def get_country(self):
        """Get the country for this address. It's fetched from
        the |citylocation|.

        :returns: the country
        """
        return self.city_location.country

    def get_state(self):
        """Get the state for this address. It's fetched from
        the |citylocation|.

        :returns: the state
        """

        return self.city_location.state

    def get_postal_code_number(self):
        """Get the postal code without any non-numeric characters.

        :returns: the postal code as a number
        """
        if not self.postal_code:
            return 0
        return int(''.join([c for c in self.postal_code
                            if c in u'1234567890']))

    def get_address_string(self):
        """Formats the address as a string

        :returns: the formatted address
        """
        return format_address(self)

    def get_details_string(self):
        """ Returns a string like ``postal_code - city - state``.
        If city or state are missing, return only postal_code; and
        if postal_code is missing, return ``city - state``, otherwise,
        return an empty string

        :returns: the detailed string
        """
        details = []
        if self.postal_code:
            details.append(self.postal_code)
        if self.city_location.city and self.city_location.state:
            details.extend([self.city_location.city,
                            self.city_location.state])
        details = u" - ".join(details)
        return details
