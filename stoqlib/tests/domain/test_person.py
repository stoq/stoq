# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Rudá Porto Filgueiras     <rudazz@gmail.com>
##            Evandro Vale Miquelito    <evandro@async.com.br>
##
##
""" Test case for stoq/domain/person.py module.  """


from stoqlib.domain.person import Person, CityLocation, Address
from stoqlib.tests.domain.base import BaseDomainTest

PHONE_DATA_VALUES = ('7133524563','1633767277')
MOBILE_DATA_VALUES = ('7188152345', '1699786748')
FAX_DATA_VALUES = ('1681359875', '1633760125')

class TestCasePerson(BaseDomainTest):
    """
    C{Person} TestCase
    """
    _table = Person

    @classmethod
    def get_extra_field_values(cls):
        return dict(phone_number=PHONE_DATA_VALUES,
                    mobile_number=MOBILE_DATA_VALUES,
                    fax_number=FAX_DATA_VALUES)

    def test_get_main_address(self):
        assert not self._instance.get_main_address()
        ctlocs = CityLocation.select(connection=self.conn)
        assert ctlocs.count() > 0
        ctloc = ctlocs[0]
        address = Address(connection=self.conn, person=self._instance,
                          city_location=ctloc, is_main_address=True)
        assert self._instance.get_main_address() is not None


    # TODO Add more tests here for the whole person module
