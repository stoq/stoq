# -*- Mode: Python; coding: iso-8859-1 -*-
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
## Author(s): Rudá Porto Filgueiras  <rudazz@gmail.com
##
"""
stoq/tests/domain/test_person.py

    Test case for stoq/domain/person.py module.
"""             
from stoq.domain.person import Person
from stoq.tests.domain.base import BaseDomainTest

PHONE_DATA_VALUES = ('7133524563','1633767277')
MOBILE_DATA_VALUES = ('7188152345', '1699786748')

class TestCasePerson(BaseDomainTest):
    """
    C{Person} TestCase
    """
    _table = Person
    person_skip_attrs = ['phone_number', 'mobile_number']
    
    def __init__(self):
        self.skip_attrs.extend(self.person_skip_attrs)
        BaseDomainTest.__init__(self)
        self._add_phone_and_mobile_values()

    def _add_phone_and_mobile_values(self):
        phone_key = self.person_skip_attrs[0]
        self.insert_dict[phone_key], self.edit_dict[phone_key] = \
                                                    PHONE_DATA_VALUES
        mobile_key = self.person_skip_attrs[1]
        self.insert_dict[mobile_key], self.edit_dict[mobile_key] = \
                                                    PHONE_DATA_VALUES
        
