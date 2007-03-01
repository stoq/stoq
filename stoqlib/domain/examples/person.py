# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Create person objects for an example database"""

import datetime
import gettext
from decimal import Decimal

from kiwi.component import provide_utility

from stoqlib.database.interfaces import ICurrentBranch, ICurrentBranchStation
from stoqlib.database.runtime import new_transaction
from stoqlib.domain.examples import log
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import (IBranch,
                                       ICompany, ISupplier,
                                       IClient, IIndividual,
                                       ICreditProvider,
                                       ITransporter)
from stoqlib.domain.station import BranchStation
from stoqlib.lib.parameters import sysparam

_ = gettext.gettext


def create_people():
    log.info('Creating person data')
    trans = new_transaction()

    person_data = [dict(name='Reginaldo Vasconcellos',
                        phone_number='5143-2587',
                        mobile_number='9112-5487',
                        email='regi@stoq.com'),
                   dict(name='Ronaldo Nazario de Lima',
                        phone_number='8722-9822',
                        mobile_number='0987-5432',
                        email='r9@stoq.com'),
                   dict(name='Elias Rodrigues de Freitas',
                        phone_number='444-2222',
                        mobile_number='9999-9999',
                        email='eli@stoq.com'),
                   dict(name='Giovana Bertolucci',
                        phone_number='1111-1111',
                        mobile_number='2222-2222',
                        email='gigi@stoq.com')]

    individual_data = [dict(cpf='234675098',
                            rg_number='222653658'),
                       dict(cpf='23487593826',
                            rg_number='447896754'),
                       dict(cpf='634423111',
                            rg_number='234568976'),
                       dict(cpf='234576849',
                            rg_number='323458382')]

    company_data = [dict(cnpj='66782278129',
                         fancy_name='RJA',
                         state_registry='0098'),
                    dict(cnpj='4444',
                         fancy_name='PlugLine',
                         state_registry='1111'),
                    dict(cnpj='777',
                         fancy_name='Buffet Italia',
                         state_registry='555'),
                    dict(cnpj='1110',
                         fancy_name='Pizzaria Donnatello',
                         state_registry='3421')]

    now = datetime.datetime.now()
    transporter_data = [dict(open_contract_date=now, is_active=False,
                             freight_percentage=Decimal('2.5')),
                        dict(open_contract_date=now + datetime.timedelta(5),
                             freight_percentage=7),
                        dict(open_contract_date=now + datetime.timedelta(10),
                             freight_percentage=Decimal('10.5')),
                        dict(open_contract_date=now + datetime.timedelta(15),
                             freight_percentage=Decimal('12.3'))]

    cityloc_data = [dict(city='Sao Paulo', country='Brazil', state='SP'),
                    dict(city='Curitiba', country='Brazil', state='PR'),
                    dict(city='Rio de Janeiro', country='Brazil', state='RJ'),
                    dict(city='Salvador', country='Brazil', state='BA')]

    address_data = [dict(street='Rua das flores', number=77,
                         district='Vila Matilde'),
                    dict(street='Rua XV de Novembro', number=278,
                         district='Centro'),
                    dict(street='Avenida Paulista', number=1533,
                         district='Brigadeiro'),
                    dict(street='Avenida Andradas', number=876,
                         district='Pinheiros')]

    finance_table = Person.getAdapterClass(ICreditProvider)
    finance_type = finance_table.PROVIDER_FINANCE

    credit_provider_data = [dict(short_name='Visa'),
                            dict(short_name='MasterCard'),
                            dict(short_name='Losango',
                                 provider_type=finance_type),
                            dict(short_name='Fininvest',
                                 provider_type=finance_type)]

    # Creating persons and facets
    for index, person_args in enumerate(person_data):
        person_obj = Person(connection=trans, **person_args)

        ctloc = CityLocation(connection=trans, **cityloc_data[index])
        address = Address(is_main_address=True,
                          person=person_obj, city_location=ctloc,
                          connection=trans, **address_data[index])

        individual_args = individual_data[index]
        person_obj.addFacet(IIndividual, connection=trans,
                            **individual_args)

        company_args = company_data[index]
        person_obj.addFacet(ICompany, connection=trans, **company_args)
        person_obj.addFacet(IClient, connection=trans)
        person_obj.addFacet(ISupplier, connection=trans)
        credit_provider = credit_provider_data[index]
        person_obj.addFacet(ICreditProvider, connection=trans,
                            open_contract_date=datetime.datetime.today(),
                            **credit_provider)

        transporter_args = transporter_data[index]
        person_obj.addFacet(ITransporter, connection=trans,
                            **transporter_args)

    # Set the manager to the last created person
    branch = sysparam(trans).MAIN_COMPANY
    branch.manager = person_obj

    trans.commit()

def create_main_branch(utilities=False):
    trans = new_transaction()
    person = Person(name=u"Async Open Source",
                    phone_number = u"33760125",
                    fax_number = u"35015394",
                    connection=trans)

    address = person.get_main_address()
    city = CityLocation(connection=trans,
                         city=u"Sao Carlos",
                         state=u"SP",
                         country=u"Brazil")
    address = Address(connection=trans,
                      is_main_address=True,
                      person=person,
                      city_location=city,
                      street=u"Orlando Damiano",
                      number=2212,
                      district=u"Jd Macarengo",
                      postal_code=u"13560-450")

    person.addFacet(ICompany, connection=trans,
                    cnpj='03.852.995/0001-07',
                    fancy_name=u"Async Open Source")
    branch = person.addFacet(IBranch, connection=trans)

    if utilities:
        provide_utility(ICurrentBranch, branch)
        station = BranchStation(name=u"Stoqlib station",
                                branch=branch,
                                connection=trans, is_active=True)
        provide_utility(ICurrentBranchStation, station)
    trans.commit()

if __name__ == "__main__":
    create_people()
