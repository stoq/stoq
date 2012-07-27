# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.address import Address, CityLocation
from stoqlib.lib.parameters import sysparam

from stoqlib.domain.test.domaintest import DomainTest


class TestCityLocation(DomainTest):
    """Tests for CityLocation class"""

    def testIsValidModel(self):
        location = self.create_city_location()
        self.failUnless(location.is_valid_model())
        invalid_location = CityLocation(connection=self.trans)
        self.failIf(invalid_location.is_valid_model())

    def testGetOrCreate(self):
        loc = CityLocation.get_or_create(self.trans, 'City',
                                         'State', 'Country')
        self.failUnless(loc)
        self.assertEqual(loc.city, 'City')
        self.assertEqual(loc.state, 'State')
        self.assertEqual(loc.country, 'Country')

        loc2 = CityLocation.get_or_create(self.trans, 'city',
                                          'state', 'country')
        self.failUnless(loc2)
        self.assertEqual(loc2.city, 'City')
        self.assertEqual(loc2.state, 'State')
        self.assertEqual(loc2.country, 'Country')
        self.assertEqual(loc2, loc)

        location = CityLocation.get_or_create(self.trans, 'São Carlos',
                                              'SP', 'Brazil')
        for city, state, country in [
            ('sao carlos', 'SP', 'Brazil'),
            ('Sao carlos', 'SP', 'Brazil'),
            ('São carlos', 'SP', 'Brazil'),
            ('sao Carlos', 'SP', 'Brazil'),
            ('sao Carlos', 'sp', 'Brazil'),
            ('sao Carlos', 'sp', 'brazil'),
            ('sao Carlos', 'Sp', 'brazil'),
            ]:
            self.assertEqual(CityLocation.get_or_create(self.trans, city,
                                                        state, country),
                             location)
        for city, state, country in [
            ('Sao', 'SP', 'Brazil'),
            ('sao', 'SP', 'Brazil'),
            ('Carlos', 'SP', 'Brazil'),
            ('carlos', 'SP', 'Brazil'),
            ]:
            self.assertNotEqual(CityLocation.get_or_create(self.trans, city,
                                                           state, country),
                                location)

    def testGetCitiesBy(self):
        location = CityLocation.get_or_create(self.trans, 'Sao Carlos',
                                              'SP', 'Brazil')
        for state, country in [
            ('SP', 'Brazil'),
            ('Sp', 'brazil'),
            ('SP', 'brazil'),
            ('sp', 'Brazil'),
            ('sp', 'BraZIL'),
            (None, 'Brazil'),
            ('SP', None),
            (None, None),
            ]:
            self.assertTrue(location.city in
                            CityLocation.get_cities_by(self.trans,
                                                       state=state,
                                                       country=country))
        for state, country in [
            ('SP', 'Brazi'),
            ('RJ', 'Brazil'),
            ('RJ', None),
            ('BA', None),
            ('SP', 'Albânia'),
            ]:
            self.assertFalse(location.city in
                             CityLocation.get_cities_by(self.trans,
                                                        state=state,
                                                        country=country))

        # Make sure no duplicates are returned
        CityLocation.get_or_create(self.trans, 'Sao Carlos', 'SP', 'BR')
        CityLocation.get_or_create(self.trans, 'Sao Carlos', 'SP', 'BR_')
        CityLocation.get_or_create(self.trans, 'Sao Carlos', 'SP', 'BR__')
        cities = list(CityLocation.get_cities_by(self.trans, state='SP'))
        self.assertEqual(len(cities), len(set(cities)))

    def testGetDefault(self):
        location = CityLocation.get_default(self.trans)
        self.failUnless(isinstance(location, CityLocation))
        self.assertEquals(location.city,
                          sysparam(self.trans).CITY_SUGGESTED)
        self.assertEquals(location.state,
                          sysparam(self.trans).STATE_SUGGESTED)
        self.assertEquals(location.country,
                          sysparam(self.trans).COUNTRY_SUGGESTED)


class TestAddress(DomainTest):
    def testIsValidModel(self):
        person = self.create_person()
        empty_location = CityLocation(connection=self.trans)
        empty_address = Address(connection=self.trans,
                                person=person,
                                city_location=empty_location)
        is_valid_model = empty_address.is_valid_model()
        assert bool(is_valid_model) is False

    def test_get_city_location_attributes(self):
        person = self.create_person()
        city = 'Acapulco'
        country = 'Brazil'
        state = 'Cracovia'
        location = CityLocation(city=city, state=state, country=country,
                                connection=self.trans)
        address = Address(person=person, city_location=location,
                          connection=self.trans)
        self.assertEquals(address.get_city(), 'Acapulco')
        self.assertEquals(address.get_country(), 'Brazil')
        self.assertEquals(address.get_state(), 'Cracovia')

    def test_get_address_string(self):
        person = self.create_person()
        location = self.create_city_location()

        street = 'Rua das Couves'
        streetnumber = 283
        district = 'Federal'
        address = Address(person=person, city_location=location,
                          street=street, streetnumber=streetnumber,
                          district=district,
                          connection=self.trans)
        string = address.get_address_string()
        self.assertEquals(string, u'%s %s, %s' % (street, streetnumber,
                                                  district))

        address.streetnumber = None
        string = address.get_address_string()
        self.assertEquals(string, u'%s %s, %s' % (street, 'N/A', district))

        address.street = ""
        string = address.get_address_string()
        self.assertEquals(string, u'')

    def testGetPostalNumber(self):
        person = self.create_person()
        location = self.create_city_location()
        address = Address(person=person, city_location=location,
                          postal_code='12345-678', connection=self.trans)

        self.assertEquals(address.get_postal_code_number(), 12345678)

    def testGetDetailsString(self):
        person = self.create_person()
        city = 'Stoqlandia'
        state = 'SP'
        country = 'Brazil'
        postal_code = '12345-678'
        location = CityLocation(city=city, state=state, country=country,
                                connection=self.trans)
        address = Address(person=person, city_location=location,
                          postal_code=postal_code, connection=self.trans)
        string = address.get_details_string()
        self.assertEquals(string, u'%s - %s - %s' % (postal_code,
                                                     city, state))
        location.city = ''
        string = address.get_details_string()
        self.assertEquals(string, u'%s' % postal_code)
        location.state = ''
        string = address.get_details_string()
        self.assertEquals(string, u'%s' % postal_code)
        address.postal_code = ''
        string = address.get_details_string()
        self.assertEquals(string, u'')
        location.city = city
        location.state = state
        string = address.get_details_string()
        self.assertEquals(string, u'%s - %s' % (city, state))
