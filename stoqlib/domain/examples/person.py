# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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

from kiwi.component import provide_utility

from stoqlib.database.interfaces import ICurrentBranch, ICurrentBranchStation
from stoqlib.database.orm import const
from stoqlib.database.runtime import new_transaction
from stoqlib.domain.examples import log
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.interfaces import (ICompany,
                                       ICreditProvider)
from stoqlib.domain.person import Person
from stoqlib.domain.station import BranchStation
from stoqlib.lib.parameters import sysparam

_ = gettext.gettext


DEFAULT_CLOSING_DAY = 12
DEFAULT_PAYMENT_DAY = 15
DEFAULT_C0MMISION = 8

DEFAULT_RECEIVE_DAY = 5

MAX_INSTALLMENTS_NUMBER = 12

def get_percentage_commission():
    percentage = (100 - DEFAULT_C0MMISION) / 100.0
    return round(percentage, 2)

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
                        email='r9@stoq.com')]

    company_data = [dict(cnpj='59.221.887/0001-90',
                         fancy_name='RJA',
                         state_registry='0098'),
                    dict(cnpj='59.221.887/0001-90',
                         fancy_name='PlugLine',
                         state_registry='1111')]

    now = const.NOW()

    cityloc_data = [dict(city='Sao Paulo', country='Brazil', state='SP'),
                    dict(city='Curitiba', country='Brazil', state='PR')]

    address_data = [dict(street='Rua das flores', streetnumber=77,
                         district='Vila Matilde'),
                    dict(street='Rua XV de Novembro', streetnumber=278,
                         district='Centro')]

    credit_provider_data = [dict(short_name='Visa'),
                            dict(short_name='MasterCard')]

    # Creating persons and facets
    for index, person_args in enumerate(person_data):
        person_obj = Person(connection=trans, **person_args)

        ctloc = CityLocation(connection=trans, **cityloc_data[index])
        address = Address(is_main_address=True,
                          person=person_obj, city_location=ctloc,
                          connection=trans, **address_data[index])

        company_args = company_data[index]
        person_obj.addFacet(ICompany, connection=trans, **company_args)

        person_obj.addFacet(ICreditProvider, connection=trans,
                            open_contract_date=datetime.datetime.today(),
                            **credit_provider_data[index])

    trans.commit()

def set_person_utilities():
    trans = new_transaction()
    branch = sysparam(trans).MAIN_COMPANY
    provide_utility(ICurrentBranch, branch)

    station = BranchStation(name=u"Stoqlib station", branch=branch,
                            connection=trans, is_active=True)
    provide_utility(ICurrentBranchStation, station)
    trans.commit()

if __name__ == "__main__":
    create_people()
