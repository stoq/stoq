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
lib/parameters.py:

    Parameters and system data for Stoq applications.


Current System parameters:

           
>> System instances:
           
    * CURRENT_BRANCH(BranchCompany): a BranchCompany instance that
                                     represents the current branch 
                                     associated with the current system 
                                     installation.

    * CURRENT_WAREHOUSE(PersonAdaptToCompany): a PersonAdaptToCompany
                                               instance that represents
                                               the company's warehouse.

    * DEFAULT_EMPLOYEE_POSITION(EmployeePosition): The employee position
                                                   suggested when we are
                                                   adding a new employee.

    * SUPPLIER_SUGGESTED(PersonAdaptToSupplier): The supplier suggested 
                                                 when we are adding a new
                                                 ProductSupplierInfo object.

    * DEFAULT_BASE_CATEGORY(BaseSellableCategory): A default base sellable
                                                   category which we always
                                                   get as a suggestion when
                                                   adding a new
                                                   SellableCategory object.
                                               
>> System constants:                                               
                                               

    * USE_LOGIC_QUANTITY(integer): an integer that defines if the company
                                   can work or not with logic quantities 
                                   during stock operations. See StockItem 
                                   documentation.

    * MAX_LATE_DAYS(integer): an integer that represents a maximum number
                              of days which a certain client can have 
                              unpaid payments with normal status.

    * ACCEPT_ORDER_PRODUCTS(integer): can this company make sales which
                                      products doensn't actually exists 
                                      in the stock ? If this parameter is 
                                      1 we can order products.

    * CITY_SUGGESTED(string): when adding a new address for a certain 
                              person we will always suggest this city.
                              
    * STATE_SUGGESTED(string): when adding a new address for a certain 
                               person we will always suggest this state.

    * COUNTRY_SUGGESTED(string): when adding a new address for a certain 
                                 person we will always suggest this country.

    * CITY_LOCATION_STATES(list): when adding a new address for a certain 
                                  person we will always show this list as
                                  available state options.

    * SELLABLE_PRICE_PRECISION(integer): precision for the price attribute 
                                         of a sellable object.

    * STOCK_BALANCE_PRECISION(integer): precision for stock balances.

    * HAS_STOCK_MODE(integer): Does this branch work with storable items ?
                               If the answer is negative, we will disable
                               stock operations in the system.

    * EDIT_SELLABLE_PRICE(integer): Can we change the price attribute
                                    of a SellableItem object during a
                                    sale ?
"""
    
import gettext

from stoqlib.exceptions import DatabaseInconsistency
from sqlobject import StringCol, IntCol

from stoq.domain.base_model import Domain
from stoq.domain.interfaces import ISupplier, IBranch, ICompany
from stoq.lib.runtime import get_connection, new_transaction


_ = gettext.gettext
__connection__ = get_connection()



#
# Infrastructure for system data
#



class ParameterData(Domain):
    """ 
    Class to store system data, such parameters. 

    field_name = the name of the parameter we want to query on
    field_value = the current result(or value) of this parameter
    foreign_key = a reference to another object used by an acessor method
                  sometimes.
    """

    field_name = StringCol(alternateID=True)
    field_value = StringCol()
    foreign_key = IntCol(default=None)


class ParameterAccess:
    """A mechanism to tie specific instances to constants that can be
    made available cross-application. This class has a special hook that
    allows the values to be looked up on-the-fly (which cuts down
    the database root to only what is actually requested) and cached.

    Usage:

        parameter = sysparam(conn).parameter_name
    """

    # Add new general settings here instead of create a single method for each
    # parameter. This is always useful when the parameter is not an object but
    # just a single string, integer or float value.
    constants = dict(USE_LOGIC_QUANTITY=1,
                     MAX_LATE_DAYS=30,
                     SELLABLE_PRICE_PRECISION=2,
                     HAS_STOCK_MODE=1,
                     STOCK_BALANCE_PRECISION=2,
                     EDIT_SELLABLE_PRICE=1,
                     ACCEPT_ORDER_PRODUCTS=1)

    def __init__(self, conn):
        self.conn = conn

    def _get_constant(self, key):
        sparam = get_parameter_by_field(key, self.conn)
        return sparam.field_value

    def get_integer_parameter(self, key):
        param = self._get_constant(key)
        try:
            param = int(param)
        except ValueError, e:
            msg = 'Parameter %s should be an integer.'
            raise ValueError(msg % key)
        return param


    
    #
    # Classmethods
    #



    @classmethod
    def ensure_general_settings(cls, conn):
        for constant, value in cls.constants.items():
            if get_parameter_by_field(constant, conn):
                continue
            set_schema(conn, constant, value)



    #
    # Properties
    #



    @property
    def SUPPLIER_SUGGESTED(self):
        from stoq.domain.person import Person
        parameter = get_foreign_key_parameter('SUPPLIER_SUGGESTED', self.conn)
        table = Person
        person_obj = table.select(table.q.id == parameter.foreign_key,
                              connection=self.conn)
        msg = 'Person object associated to this supplier not found.'
        assert person_obj and person_obj.count() == 1, msg
        supplier = ISupplier(person_obj[0], connection=self.conn)
        assert supplier, 'Supplier rule for the selected person not found.'
        return supplier

    @property
    def CITY_LOCATION_STATES(self):
        return [ 'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
                 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
                 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO' ]

    @property
    def CURRENT_BRANCH(self):
        from stoq.domain.person import Person
        parameter = get_foreign_key_parameter('CURRENT_BRANCH', 
                                              self.conn)
        table = Person
        person_obj = table.select(table.q.id == parameter.foreign_key,
                                  connection=self.conn)
        msg = 'Person object associated to this branch not found.'
        assert person_obj and person_obj.count() == 1, msg
        branch = IBranch(person_obj[0], connection=self.conn)
        assert branch, 'Branch rule for the selected person not found.'
        return branch

    @property
    def DEFAULT_BASE_CATEGORY(self):
        from stoq.domain.sellable import BaseSellableCategory
        parameter = get_foreign_key_parameter('DEFAULT_BASE_CATEGORY', 
                                              self.conn)
        table = BaseSellableCategory
        base_cat = table.select(table.q.id == parameter.foreign_key,
                                connection=self.conn)
        assert base_cat.count() == 1, 'Base category not found.'
        return base_cat[0]

    @property
    def DEFAULT_EMPLOYEE_POSITION(self):
        from stoq.domain.person import EmployeePosition
        parameter = get_foreign_key_parameter('DEFAULT_EMPLOYEE_POSITION', 
                                              self.conn)
        table = EmployeePosition
        position = table.select(table.q.id == parameter.foreign_key,
                                connection=self.conn)
        assert position.count() == 1, 'Employee position not found.'
        return position[0]

    @property
    def CURRENT_WAREHOUSE(self):
        from stoq.domain.person import Person
        parameter = get_foreign_key_parameter('CURRENT_WAREHOUSE', 
                                              self.conn)
        table = Person
        person_obj = table.select(table.q.id == parameter.foreign_key,
                                  connection=self.conn)
        msg = 'Person object associated to this warehouse not found.'
        assert person_obj and person_obj.count() == 1, msg
        warehouse = ICompany(person_obj[0], connection=self.conn)
        assert warehouse, 'Warehouse associated to the selected person not found.'
        return warehouse

    @property
    def USE_LOGIC_QUANTITY(self):
        return self.get_integer_parameter('USE_LOGIC_QUANTITY')

    @property
    def MAX_LATE_DAYS(self):
        return self.get_integer_parameter('MAX_LATE_DAYS')
        
    @property
    def ACCEPT_ORDER_PRODUCTS(self):
        return self.get_integer_parameter('ACCEPT_ORDER_PRODUCTS')

    @property
    def CITY_SUGGESTED(self):
        return self._get_constant('CITY_SUGGESTED')

    @property
    def STATE_SUGGESTED(self):
        return self._get_constant('STATE_SUGGESTED')

    @property
    def COUNTRY_SUGGESTED(self):
        return self._get_constant('COUNTRY_SUGGESTED')

    @property
    def SELLABLE_PRICE_PRECISION(self):
        return self.get_integer_parameter('SELLABLE_PRICE_PRECISION')

    @property
    def HAS_STOCK_MODE(self):
        return self.get_integer_parameter('HAS_STOCK_MODE')

    @property
    def STOCK_BALANCE_PRECISION(self):
        return self.get_integer_parameter('STOCK_BALANCE_PRECISION')

    @property
    def EDIT_SELLABLE_PRICE(self):
        return self.get_integer_parameter('EDIT_SELLABLE_PRICE')


def sysparam(conn):
    return ParameterAccess(conn)


def get_parameter_by_field(field_name, conn):
    values = ParameterData.select(ParameterData.q.field_name == field_name,
                                  connection=conn)
    if values.count() > 1:
        msg = ('There is no unique correspondent parameter for this field '
               'name. Found %s items.' % values.count())
        DatabaseInconsistency(msg)
    elif not values.count():
        return None
    return values[0]


def get_foreign_key_parameter(field_name, conn):
    parameter = get_parameter_by_field(field_name, conn)
    if not (parameter and parameter.foreign_key):
        msg = _('There is no defined %s parameter data'
                'in the database.' % field_name)
        raise DatabaseInconsistency(msg)
    return parameter



#
# Creating system data
#



def set_schema(conn, field_name, field_value, foreign_key=None):
    ParameterData(connection=conn, field_name=field_name, 
                  field_value=field_value, foreign_key=foreign_key)


def ensure_supplier_suggested(conn):
    from stoq.domain.person import Person
    key = "SUPPLIER_SUGGESTED"
    if get_parameter_by_field(key, conn):
        return
    person_obj = Person(name=key, connection=conn)
    person_obj.addFacet(ICompany, cnpj='supplier suggested', connection=conn)
    person_obj.addFacet(ISupplier, connection=conn)
    set_schema(conn, key, 'get_supplier_suggested', 
               foreign_key=person_obj.id)


def ensure_default_base_category(conn):
    from stoq.domain.sellable import (BaseSellableCategory,
                                           AbstractSellableCategory)
    key = "DEFAULT_BASE_CATEGORY"
    if get_parameter_by_field(key, conn):
        return
    table = AbstractSellableCategory
    abstract_cat = table(connection=conn, description=key)
    table = BaseSellableCategory
    base_cat = table(connection=conn, category_data=abstract_cat)
    set_schema(conn, key, 'get_default_base_category', 
               foreign_key=base_cat.id)


def ensure_default_employee_position(conn):
    from stoq.domain.person import EmployeePosition
    key = "DEFAULT_EMPLOYEE_POSITION"
    if get_parameter_by_field(key, conn):
        return
    position = EmployeePosition(name='Sales Person', connection=conn)
    set_schema(conn, key, 'get_default_employee_position', 
               foreign_key=position.id)


def ensure_current_branch(conn):
    from stoq.domain.person import Person
    key = "CURRENT_BRANCH"
    if get_parameter_by_field(key, conn):
        return
    person_obj = Person(name=key, connection=conn)
    # XXX Ok, I know. 'current_branch' is not a valid cnpj but as I don't know
    # what is the cnpj of this company I need to put something there because
    # this is a mandatory field. I think use a simple string could help user
    # to fix this field later.
    person_obj.addFacet(ICompany, cnpj='current_branch', connection=conn)
    person_obj.addFacet(IBranch, connection=conn)
    set_schema(conn, key, 'get_current_branch', 
               foreign_key=person_obj.id)               


def ensure_current_warehouse(conn):
    from stoq.domain.person import Person
    key = "CURRENT_WAREHOUSE"
    if get_parameter_by_field(key, conn):
        return
    person_obj = Person(name=key, connection=conn)
    # XXX See ensure_current_branch comment: we have the same problem with
    # cnpj here.
    person_obj.addFacet(ICompany, cnpj='current_warehouse', connection=conn)
    set_schema(conn, key, 'get_current_warehouse', 
               foreign_key=person_obj.id)


def ensure_city_location(conn):
    city_data = ("CITY_SUGGESTED", 'Belo Horizonte')
    state_data = ("STATE_SUGGESTED", 'MG')
    country_data = ("COUNTRY_SUGGESTED", 'Brasil')

    values = [city_data, state_data, country_data]
    for key, data in values:
        if get_parameter_by_field(key, conn):
            return
    
    for key, data in values:
        set_schema(conn, key, data)



#
# Ensuring everything
#



def ensure_system_parameters():
    trans = new_transaction()

    ParameterAccess.ensure_general_settings(trans)
    ensure_default_employee_position(trans)
    ensure_supplier_suggested(trans)
    ensure_default_base_category(trans)
    ensure_current_branch(trans)
    ensure_current_warehouse(trans)
    ensure_city_location(trans)

    trans.commit()
