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
from stoqlib.domain.person import Company, Branch, LoginUser, Person
from stoqlib.importers.csvimporter import CSVImporter
from stoqlib.lib.parameters import sysparam


class BranchImporter(CSVImporter):
    fields = ['name',
              'fancy_name',
              'phone_number',
              'fax_number',
              'state_registry',
              'cnpj',
              'city',
              'country',
              'state',
              'street',
              'streetnumber',
              'district',
              'postal_code',
              ]

    branches = []

    def process_one(self, data, fields, store):
        person = Person(
            store=store,
            name=data.name,
            phone_number=data.phone_number,
            fax_number=data.fax_number)

        Company(person=person, cnpj=data.cnpj,
                state_registry=data.state_registry,
                fancy_name=data.fancy_name,
                store=store)

        ctloc = CityLocation.get_or_create(store=store,
                                           city=data.city,
                                           state=data.state,
                                           country=data.country)
        streetnumber = data.streetnumber and int(data.streetnumber) or None
        Address(
            is_main_address=True,
            person=person,
            city_location=ctloc,
            store=store,
            street=data.street,
            streetnumber=streetnumber,
            district=data.district,
            postal_code=data.postal_code
        )

        branch = Branch(person=person, store=store)
        for user in store.find(LoginUser):
            user.add_access_to(branch)
        self.branches.append(branch)

    def when_done(self, store):
        if sysparam.has_object('MAIN_COMPANY'):
            return

        if not self.branches:
            return

        sysparam.set_object(store, 'MAIN_COMPANY', self.branches[0])
        assert sysparam.has_object('MAIN_COMPANY')
