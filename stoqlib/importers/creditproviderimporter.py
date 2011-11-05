# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2008 Async Open Source
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

from stoqlib.database.orm import const
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.interfaces import ICompany, ICreditProvider
from stoqlib.domain.person import Person
from stoqlib.importers.csvimporter import CSVImporter


class CreditProviderImporter(CSVImporter):
    fields = ['name',
              'phone_number',
              'mobile_number',
              'email',
              'cnpj',
              'fancy_name',
              'state_registry',
              'city',
              'country',
              'state',
              'street',
              'streetnumber',
              'district',
              'provider_name']

    def process_one(self, data, fields, trans):
        person = Person(
            connection=trans,
            name=data.name,
            phone_number=data.phone_number,
            mobile_number=data.mobile_number)

        person.addFacet(ICompany,
                        connection=trans,
                        cnpj=data.cnpj,
                        fancy_name=data.fancy_name,
                        state_registry=data.state_registry)

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

        person.addFacet(ICreditProvider, connection=trans,
                        open_contract_date=const.NOW(),
                        short_name=data.provider_name)
