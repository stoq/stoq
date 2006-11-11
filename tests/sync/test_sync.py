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
## Author(s): Johan Dahlin            <jdahlin@async.com.br>
##

from stoqlib.database.runtime import get_connection, new_transaction
from stoqlib.domain.interfaces import (IEmployee, ISalesPerson, IUser,
                                       IIndividual)
from stoqlib.domain.person import EmployeeRole, Person
from stoqlib.domain.profile import UserProfile

from tests.sync.base import SyncTest

class TestUpdate(SyncTest):
    #
    # Synchronization tests.
    #
    # You are allowed to commit here
    #
    # What you cannot depend on is the order the tests will
    # be executed in, so you cannot use objects defined outside
    # of the current test function
    #
    def testSimple(self):
        self.switch_to_office()
        trans = new_transaction()
        person = Person(name="Test Person", connection=trans)
        trans.commit()

        self.update("shop-computer")

        self.switch_to_shop()
        trans = new_transaction()
        self.failUnless(
            Person.selectOneBy(name="Test Person",
                               connection=new_transaction()))

    def testDuplex(self):
        # Shop
        self.switch_to_shop()
        trans = new_transaction()
        person = Person(name="Person 1", connection=trans)
        trans.commit()

        # Office
        self.switch_to_office()
        trans = new_transaction()
        person = Person(name="Person 2", connection=trans)
        trans.commit()

        self.update("shop-computer")

        self.failUnless(Person.selectOneBy(name="Person 1",
                                           connection=get_connection()))

        # Shop
        self.switch_to_shop()
        self.failUnless(Person.selectOneBy(name="Person 2",
                                           connection=get_connection()))

    def testFacet(self):
        # Create a person in the shop which is "sleeping"
        # Create a person in the office which is "working"

        # Shop
        self.switch_to_shop()
        trans = new_transaction()
        person = Person(name="Person 3", connection=trans)
        person.addFacet(IIndividual, occupation="Sleeping",
                        connection=trans)
        trans.commit()

        # Office
        self.switch_to_office()
        trans = new_transaction()
        person = Person(name="Person 4", connection=trans)
        person.addFacet(IIndividual, occupation="Working",
                        connection=trans)
        trans.commit()

        self.update("shop-computer")
        conn = get_connection()
        self.failUnless(Person.selectOneBy(name="Person 3", connection=conn))
        self.failUnless(Person.iselectOneBy(IIndividual, occupation="Sleeping",
                                            connection=conn))

        # Shop
        self.switch_to_shop()
        conn = get_connection()
        self.failUnless(Person.selectOneBy(name="Person 4",
                                           connection=conn))
        self.failUnless(Person.iselectOneBy(IIndividual, occupation="Working",
                                            connection=conn))

    def testDifferentFacets(self):
        # Create a person with an employee facet in the shop
        # Sync with office
        # Make him a salesperson in the office
        # Make him a user in the store

        # Shop
        self.switch_to_shop()
        trans = new_transaction()
        person = Person(name="Employee", connection=trans)
        person.addFacet(IIndividual, connection=trans)
        role = EmployeeRole.selectOneBy(name="Clerk", connection=trans)
        person.addFacet(IEmployee, role=role, connection=trans)
        trans.commit()

        # Office
        self.switch_to_office()
        self.update("shop-computer")

        trans = new_transaction()
        person = Person.selectOneBy(name="Employee", connection=trans)
        self.failUnless(person)
        person.addFacet(ISalesPerson, comission=10, connection=trans)
        trans.commit()

        # Shop
        self.switch_to_shop()
        trans = new_transaction()
        person = Person.selectOneBy(name="Employee", connection=trans)
        self.failUnless(person)
        profile = UserProfile.selectOneBy(name='Administrator', connection=trans)
        person.addFacet(IUser, username="username", password="password",
                        profile=profile, connection=trans)
        trans.commit()

        # Office
        self.switch_to_office()
        self.update("shop-computer")

        person = Person.selectOneBy(name="Employee", connection=trans)
        self.failUnless(person)
        user = IUser(person, None)
        self.failUnless(user)
        self.assertEquals(user.username, "username")

        # Shop
        self.switch_to_shop()
        person = Person.selectOneBy(name="Employee", connection=trans)
        self.failUnless(person)
        salesperson = ISalesPerson(person, None)
        self.failUnless(salesperson)
        self.assertEquals(salesperson.comission, 10)

