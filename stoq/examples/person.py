#!/usr/bin/env python
# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
"""
stoq/examples/person.py:

    Create person objects for an example database.
"""

from stoq.domain.person import Person, EmployeePosition
from stoq.domain.interfaces import (ICompany, ISupplier, IBranch, 
                                    IClient, IIndividual, 
                                    IEmployee, ISalesPerson,
                                    IUser)
from stoq.lib.runtime import new_transaction

def create_persons():
    print 'Creating persons...'
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

    user_data = [dict(username='john',
                      password='john243'),
                 dict(username='michey', 
                      password='mouse88'),
                 dict(username='dude', 
                      password='dude43'),
                 dict(username='maddog', 
                      password='dog54')]

    # Creating persons and facets
    index = 0
    for person_args in person_data:
        person_obj = Person(connection=trans, **person_args)
        
        individual_args = individual_data[index]
        person_obj.addFacet(IIndividual, connection=trans, 
                            **individual_args)

        company_args = company_data[index]
        person_obj.addFacet(ICompany, connection=trans, 
                            **company_args)

        person_obj.addFacet(IClient, connection=trans)
        person_obj.addFacet(ISupplier, connection=trans)
        person_obj.addFacet(IBranch, connection=trans)

        position_args = position_data[index]
        position = EmployeePosition(connection=trans,
                                    **position_args)
        employee_args = employee_data[index]
        person_obj.addFacet(IEmployee, connection=trans,
                            position=position,
                            **employee_args)
        # SalesPerson facet requires an employee facet.
        person_obj.addFacet(ISalesPerson, connection=trans)

        user_args = user_data[index]
        person_obj.addFacet(IUser, connection=trans, 
                            **user_args)
        index += 1
        
    trans.commit()
    print 'done.'


if __name__ == "__main__":
    create_persons()
