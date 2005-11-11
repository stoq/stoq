#!/usr/bin/env python
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
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
"""
stoq/examples/person.py:

    Create person objects for an example database.
"""

import datetime

from stoq.lib.runtime import new_transaction, print_msg
from stoq.domain.profile import UserProfile
from stoq.domain.person import (Person, EmployeeRole, Address,
                                CityLocation)
from stoq.domain.interfaces import (ICompany, ISupplier, IBranch, 
                                    IClient, IIndividual, 
                                    IEmployee, ISalesPerson,
                                    IUser, ICreditProvider, ITransporter)

def create_persons():
    print_msg('Creating persons...', break_line=False)
    trans = new_transaction()

    person_data = [dict(name='John Wayne', 
                        phone_number='5143-2587',
                        mobile_number='9112-5487',
                        email='someone@stoq.com'),
                   dict(name='Mickey Mouse', 
                        phone_number='8722-9822',
                        mobile_number='0987-5432',
                        email='mouse@stoq.com'),
                   dict(name='The dude',
                        phone_number='444-2222',
                        mobile_number='9999-9999',
                        email='dude@stoq.com'),
                   dict(name='Mad dog', 
                        phone_number='1111-1111',
                        mobile_number='2222-2222',
                        email='crazy@stoq.com')]

    individual_data = [dict(cpf='012XX', 
                            rg_number='48Y'),
                       dict(cpf='98VV', 
                            rg_number='AR5T'),
                       dict(cpf='WWT', 
                            rg_number='M8923'),
                       dict(cpf='9999', 
                            rg_number='4444')]

    company_data = [dict(cnpj='2222', 
                         fancy_name='Wayne Company',
                         state_registry='0098'),
                    dict(cnpj='4444', 
                         fancy_name='Mouse Ltd',
                         state_registry='1111'),
                    dict(cnpj='777', 
                         fancy_name='Dude Corporation',
                         state_registry='555'),
                    dict(cnpj='1110', 
                         fancy_name='Dog Ltd',
                         state_registry='3421')]

    position_data = [dict(name='SalesPerson'),
                     dict(name='Manager'),
                     dict(name='Secretary'), 
                     dict(name='Director')]

    employee_data = [dict(registry_number='00099'), 
                     dict(registry_number='7777'),
                     dict(registry_number='6666'),
                     dict(registry_number='5555')]

    now = datetime.datetime.now()
    transporter_data = [dict(open_contract_date=now, is_active=False,
                             freight_percentage=2.5),
                        dict(open_contract_date=now + datetime.timedelta(5),
                             freight_percentage=7.0),
                        dict(open_contract_date=now + datetime.timedelta(10),
                             freight_percentage=10.5),
                        dict(open_contract_date=now + datetime.timedelta(15),
                             freight_percentage=12.3)]

    user_data = [dict(username='john',
                      password='john243'),
                 dict(username='michey', 
                      password='mouse88'),
                 dict(username='dude', 
                      password='dude43'),
                 dict(username='maddog', 
                      password='dog54')]

    cityloc_data = [dict(city='Belo Horizonte', country='Brasil', 
                         state='MG'),
                    dict(city='Curitiba', country='Brasil', state='PR'),
                    dict(city='Rio de Janeiro', country='Brasil', state='RJ'),
                    dict(city='Salvador', country='Brasil', state='BA')]

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

    profile_names = ['Salesperson', 'Manager', 'Secretary', 'Trainee']

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
        person_obj.addFacet(ICompany, connection=trans, 
                            **company_args)

        person_obj.addFacet(IClient, connection=trans)
        person_obj.addFacet(ISupplier, connection=trans)
        person_obj.addFacet(IBranch, connection=trans)

        credit_provider = credit_provider_data[index]
        person_obj.addFacet(ICreditProvider, connection=trans,
                            open_contract_date=datetime.datetime.today(),
                            **credit_provider)

        position_args = position_data[index]
        role = EmployeeRole(connection=trans, **position_args)
        employee_args = employee_data[index]
        person_obj.addFacet(IEmployee, connection=trans, role=role,
                            **employee_args)
        # SalesPerson facet requires an employee facet.
        person_obj.addFacet(ISalesPerson, connection=trans)

        prof_name = profile_names[index]
        # The True argument here means full permition for this profile. 
        # This is useful when testing all the fetuares of Stoq applications
        profile = UserProfile.create_profile_template(trans, prof_name, 
                                                      True)
        user_args = user_data[index]
        person_obj.addFacet(IUser, connection=trans, profile=profile,
                            **user_args)
        transporter_args = transporter_data[index]
        person_obj.addFacet(ITransporter, connection=trans,
                            **transporter_args)
        
    trans.commit()
    print_msg('done.')


if __name__ == "__main__":
    create_persons()
