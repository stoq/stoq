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
from stoqlib.domain.person import Company, Supplier, Person
from stoqlib.importers.csvimporter import CSVImporter
from stoqlib.lib.parameters import sysparam


class SupplierImporter(CSVImporter):
    fields = ['name',
              'phone_number',
              'mobile_number',
              'email',
              'cnpj',
              'state_registry',
              'city',
              'country',
              'state',
              'street',
              'streetnumber',
              'district']

    suppliers = []

    def process_one(self, data, fields, store):
        person = Person(
            store=store,
            name=data.name,
            phone_number=data.phone_number,
            mobile_number=data.mobile_number)

        Company(person=person,
                store=store,
                cnpj=data.cnpj,
                fancy_name=data.name,
                state_registry=data.state_registry)

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
            district=data.district
        )

        supplier = Supplier(person=person, store=store)
        self.suppliers.append(supplier)

    def when_done(self, store):
        if sysparam.has_object('SUGGESTED_SUPPLIER'):
            return

        if not self.suppliers:
            return
        sysparam.set_object(store, 'SUGGESTED_SUPPLIER', self.suppliers[0])
