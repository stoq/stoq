# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.person import (Employee, EmployeeRole, EmployeeRoleHistory,
                                   Individual, LoginUser, Person,
                                   SalesPerson)
from stoqlib.domain.profile import UserProfile
from stoqlib.importers.csvimporter import CSVImporter


class EmployeeImporter(CSVImporter):
    fields = ['name',
              'phone_number',
              'mobile_number',
              'email',
              'rg',
              'cpf',
              'role',
              'employee_number',
              'start',
              'salary',
              'city',
              'country',
              'state',
              'street',
              'streetnumber',
              'district',
              'profile',
              'username',
              'password']

    def process_one(self, data, fields, store):
        person = Person(
            store=store,
            name=data.name,
            phone_number=data.phone_number,
            mobile_number=data.mobile_number)

        Individual(person=person,
                   store=store,
                   cpf=data.cpf,
                   rg_number=data.rg)

        role = EmployeeRole(store=store, name=data.role)

        employee = Employee(person=person,
                            store=store,
                            role=role,
                            salary=int(data.salary),
                            registry_number=data.employee_number)

        start = self.parse_date(data.start)
        EmployeeRoleHistory(
            store=store, role=role,
            employee=employee,
            is_active=True,
            began=start,
            salary=int(data.salary))

        ctloc = CityLocation.get_or_create(store=store,
                                           city=data.city,
                                           state=data.state,
                                           country=data.country)
        streetnumber = data.streetnumber and int(data.streetnumber) or None
        Address(is_main_address=True,
                person=person,
                city_location=ctloc,
                store=store,
                street=data.street,
                streetnumber=streetnumber,
                district=data.district)

        profile = store.find(UserProfile, name=data.profile).one()

        LoginUser(person=person, store=store, profile=profile,
                  username=data.username,
                  password=data.password)
        SalesPerson(person=person, store=store)
