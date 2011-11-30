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
from stoqlib.domain.interfaces import (IIndividual, IEmployee, IUser,
                                       ISalesPerson)
from stoqlib.domain.person import Person, EmployeeRole, EmployeeRoleHistory
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

    def process_one(self, data, fields, trans):
        person = Person(
            connection=trans,
            name=data.name,
            phone_number=data.phone_number,
            mobile_number=data.mobile_number)

        person.addFacet(IIndividual,
                        connection=trans,
                        cpf=data.cpf,
                        rg_number=data.rg)

        role = EmployeeRole(connection=trans, name=data.role)

        employee = person.addFacet(IEmployee,
                                   connection=trans,
                                   role=role,
                                   salary=int(data.salary),
                                   registry_number=data.employee_number)

        start = self.parse_date(data.start)
        EmployeeRoleHistory(
            connection=trans, role=role,
            employee=employee,
            is_active=True,
            began=start,
            salary=int(data.salary))

        ctloc = CityLocation.get_or_create(trans=trans,
                                           city=data.city,
                                           state=data.state,
                                           country=data.country)
        streetnumber = data.streetnumber and int(data.streetnumber) or None
        Address(is_main_address=True,
                person=person,
                city_location=ctloc,
                connection=trans,
                street=data.street,
                streetnumber=streetnumber,
                district=data.district)

        profile = UserProfile.selectOneBy(name=data.profile, connection=trans)

        person.addFacet(IUser, connection=trans, profile=profile,
                        username=data.username,
                        password=data.password)
        person.addFacet(ISalesPerson, connection=trans)
