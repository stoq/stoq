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
## Author(s):    Evandro Vale Miquelito     <evandro@async.com.br>
##               Henrique Romano            <henrique@async.com.br>
##
"""
lib/parameters.py:

    Parameters and system data for Stoq applications.


Current System parameters:

           
>> System instances:
           
    * CURRENT_BRANCH(PersonAdaptToBranch): a BranchCompany instance that
                                           represents the current branch
                                           associated with the current 
                                           system installation.

    * CURRENT_WAREHOUSE(PersonAdaptToCompany): a PersonAdaptToCompany
                                               instance that represents
                                               the company's warehouse.

    * DEFAULT_EMPLOYEE_ROLE(EmployeeRole): The employee role
                                                   suggested when we are
                                                   adding a new employee.

    * SUGGESTED_SUPPLIER(PersonAdaptToSupplier): The supplier suggested 
                                                 when we are adding a new
                                                 ProductSupplierInfo object.

    * DEFAULT_BASE_CATEGORY(BaseSellableCategory): A default base sellable
                                                   category which we always
                                                   get as a suggestion when
                                                   adding a new
                                                   SellableCategory object.
                                                   
    * DEFAULT_PAYMENT_DESTINATION(PaymentDestination): A default payment
                                                       destination which
                                                       will be used for all
                                                       the created payments
                                                       until the user change
                                                       the destination of
                                                       each payment method.

    * BASE_PAYMENT_METHOD(PaymentMethod): The base payment method which can
                                          easily be converted to other methods 
                                          like check and bill.

    * METHOD_MONEY(PMAdaptToMoneyPM): Definition of the money payment 
                                      method.

    * DELIVERY_SERVICE(Service): The default delivery service
                                 to the system.

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

    * SELLABLE_PRICE_PRECISION(integer): precision for the price attribute 
                                         of a sellable object.

    * STOCK_BALANCE_PRECISION(integer): precision for stock balances.

    * PAYMENT_PRECISION(integer): precision for payment values.

    * HAS_DELIVERY_MODE(integer): If this branch works with service
                                  delivery.

    * HAS_STOCK_MODE(integer): Does this branch work with storable items ?
                               If the answer is negative, we will disable
                               stock operations in the system.

    * EDIT_SELLABLE_PRICE(integer): Can we change the price attribute
                                    of a SellableItem object during a
                                    sale ?

    * MAX_SEARCH_RESULTS(integer): The maximum number of results we must
                                   show after searching in a SearchBar.

    * MANDATORY_INTEREST_CHARGE(integer): Once this paramter is set, the
                                          charge of monthly interest is
                                          mandatory for every payment

    * COMPARISON_FLOAT_TOLERANCE(float): This is useful when performin 
                                         comparison between two float 
                                         numbers. 
                                         If abs(numberA - numberB) = 
                                         COMPARISON_FLOAT_TOLERANCE
                                         the two numbers can be considerer

    * CONFIRM_SALES_ON_TILL(integer): Once this parameter is set, the sales
                                      confirmation are only made on till
                                      application

    * SET_PAYMENT_METHODS_ON_TILL(integer): Do not show payment method
                                            definitions step on SaleWizard
                                            through POS application if
                                            CONFIRM_SALES_ON_TILL is set.
                                            This step will only be show on
                                            Till application.

    * USE_PURCHASE_PREVIEW_PAYMENTS(integer): Generate preview payments for
                                              new purchases which are not
                                              received yet. Once the order
                                              is received the preview
                                              payments will be also
                                              confirmed as valid payments
                                              with STATuS_TO_PAY
"""
    
import gettext

from stoqlib.exceptions import DatabaseInconsistency
from sqlobject import StringCol
from kiwi.python import namedAny, ClassInittableObject

from stoq.domain.base import Domain, AbstractModel
from stoq.domain.interfaces import (ISupplier, IBranch, ICompany, ISellable,
                                    IMoneyPM, ICheckPM, IBillPM, ICardPM,
                                    IFinancePM)
from stoq.lib.runtime import new_transaction, print_msg


_ = gettext.gettext



#
# Infrastructure for system data
#



class ParameterData(Domain):
    """ 
    Class to store system data, such parameters. 

    field_name = the name of the parameter we want to query on
    field_value = the current result(or value) of this parameter
    """

    field_name = StringCol(alternateID=True)
    field_value = StringCol()

class ParameterAttr:
    def __init__(self, key, type, initial=None):
        self.key = key
        self.type = type
        self.initial = initial


class ParameterAccess(ClassInittableObject):
    """A mechanism to tie specific instances to constants that can be
    made available cross-application. This class has a special hook that
    allows the values to be looked up on-the-fly and cached.

    Usage:

        parameter = sysparam(conn).parameter_name
    """

    # New parameters must always be defined here
    constants = [# Adding constants
                 ParameterAttr('USE_LOGIC_QUANTITY', int, 
                               initial=True),
                 ParameterAttr('MAX_LATE_DAYS', int, 
                               initial=30),
                 ParameterAttr('SELLABLE_PRICE_PRECISION', int, 
                               initial=2),
                 ParameterAttr('HAS_STOCK_MODE', int, 
                               initial=True),
                 ParameterAttr('HAS_DELIVERY_MODE', int, 
                               initial=True),
                 ParameterAttr('STOCK_BALANCE_PRECISION', int, 
                               initial=2),
                 ParameterAttr('PAYMENT_PRECISION', int, 
                               initial=2),
                 ParameterAttr('EDIT_SELLABLE_PRICE', int, 
                               initial=True),
                 ParameterAttr('ACCEPT_ORDER_PRODUCTS', int, 
                               initial=True),
                 ParameterAttr('MAX_SEARCH_RESULTS', int, 
                               initial=600),
                 ParameterAttr('COMPARISON_FLOAT_TOLERANCE', float, 
                               initial=0.02),
                 ParameterAttr('CITY_SUGGESTED', str, 
                               initial='Belo Horizonte'),
                 ParameterAttr('STATE_SUGGESTED', str, 
                               initial='MG'),
                 ParameterAttr('COUNTRY_SUGGESTED', str, 
                               initial='Brasil'),
                 ParameterAttr('CONFIRM_SALES_ON_TILL', int, 
                               initial=True),
                 ParameterAttr('MANDATORY_INTEREST_CHARGE', int, 
                               initial=False),
                 ParameterAttr('USE_PURCHASE_PREVIEW_PAYMENTS', int, 
                               initial=True),
                 ParameterAttr('SET_PAYMENT_METHODS_ON_TILL', int, 
                               initial=True),

                 # Adding objects
                 ParameterAttr('SUGGESTED_SUPPLIER', 
                               'person.PersonAdaptToSupplier'),
                 ParameterAttr('CURRENT_BRANCH', 
                               'person.PersonAdaptToBranch'),
                 ParameterAttr('DEFAULT_BASE_CATEGORY', 
                               'sellable.BaseSellableCategory'),
                 ParameterAttr('DEFAULT_EMPLOYEE_ROLE', 
                               'person.EmployeeRole'),
                 ParameterAttr('DEFAULT_PAYMENT_DESTINATION', 
                               'payment.destination.PaymentDestination'),
                 ParameterAttr('BASE_PAYMENT_METHOD', 
                               'payment.methods.PaymentMethod'),
                 ParameterAttr('METHOD_MONEY', 
                               'payment.methods.PMAdaptToMoneyPM'),
                 ParameterAttr('DELIVERY_SERVICE', 
                               'service.Service'),
                 ParameterAttr('CURRENT_WAREHOUSE', 
                               'person.PersonAdaptToCompany')]

    _cache = {}

    def __init__(self, conn):
        self.conn = conn
    
    @classmethod
    def __class_init__(cls, namespace):
        for obj in cls.constants:
            prop = property(lambda self, n=obj.key, v=obj.type:
                            self.get_parameter_by_field(n, v))
            setattr(cls, obj.key, prop)

    def set_schema(self, field_name, field_value):
        ParameterData(connection=self.conn, field_name=field_name, 
                      field_value=field_value)
        
    def get_parameter_by_field(self, field_name, field_type): 
        if type(field_type) == str:
            field_type = namedAny('stoq.domain.' + field_type)

        if self._cache.has_key(field_name):
            param = self._cache[field_name]
            if issubclass(field_type, AbstractModel):
                return field_type.get(param.id, connection=self.conn)
            return param

        values = ParameterData.select(ParameterData.q.field_name == field_name,
                                      connection=self.conn)
        if values.count() > 1:
            msg = ('There is no unique correspondent parameter for this field '
                   'name. Found %s items.' % values.count())
            DatabaseInconsistency(msg)
        elif not values.count():
            return None

        value = values[0]
        if issubclass(field_type, AbstractModel):
            param = field_type.get(value.field_value, connection=self.conn)
        else:
            param = field_type(value.field_value)

        self._cache[field_name] = param
        return param


    def set_defaults(self):
        constants = [c for c in self.constants if c.initial is not None]
        
        # Creating constants
        for obj in constants:
            if self.get_parameter_by_field(obj.key, obj.type):
                continue
            if obj.type is int:
                # Convert Bool to int here
                value = int(obj.initial)
            else:
                value = obj.initial
            self.set_schema(obj.key, value)

        # Creating system objects
        # When creating new methods for system objects creation add them 
        # always here
        self.ensure_suggested_supplier()
        self.ensure_default_base_category()
        self.ensure_default_employee_role()
        self.ensure_current_branch()
        self.ensure_current_warehouse()
        self.ensure_payment_destination()
        self.ensure_payment_methods()
        self.ensure_delivery_service()



    #
    # Methods for system objects creation
    #

    def ensure_suggested_supplier(self):
        from stoq.domain.person import Person, PersonAdaptToSupplier
        key = "SUGGESTED_SUPPLIER"
        if self.get_parameter_by_field(key, PersonAdaptToSupplier):
            return
        person_obj = Person(name=key, connection=self.conn)
        person_obj.addFacet(ICompany, cnpj='supplier suggested', 
                            connection=self.conn)
        supplier = person_obj.addFacet(ISupplier, connection=self.conn)
        self.set_schema(key, supplier.id)

    def ensure_default_base_category(self):
        from stoq.domain.sellable import (BaseSellableCategory,
                                          AbstractSellableCategory)
        key = "DEFAULT_BASE_CATEGORY"
        if self.get_parameter_by_field(key, BaseSellableCategory):
            return
        abstract_cat = AbstractSellableCategory(connection=self.conn, 
                                                description=key)
        base_cat = BaseSellableCategory(connection=self.conn, 
                                        category_data=abstract_cat)
        self.set_schema(key, base_cat.id)

    def ensure_default_employee_role(self):
        from stoq.domain.person import EmployeeRole
        key = "DEFAULT_EMPLOYEE_ROLE"
        if self.get_parameter_by_field(key, EmployeeRole):
            return
        role = EmployeeRole(name='Sales Person', 
                                    connection=self.conn)
        self.set_schema(key, role.id)

    def ensure_current_branch(self):
        from stoq.domain.person import Person, PersonAdaptToBranch
        key = "CURRENT_BRANCH"
        if self.get_parameter_by_field(key, PersonAdaptToBranch):
            return
        person_obj = Person(name=key, connection=self.conn)
        # XXX Ok, I know. 'current_branch' is not a valid cnpj but as I don't know
        # what is the cnpj of this company I need to put something there because
        # this is a mandatory field. I think use a simple string could help user
        # to fix this field later.
        person_obj.addFacet(ICompany, cnpj='current_branch', 
                            connection=self.conn)
        branch = person_obj.addFacet(IBranch, connection=self.conn)
        self.set_schema(key, branch.id)               

    def ensure_current_warehouse(self):
        from stoq.domain.person import Person, PersonAdaptToCompany
        key = "CURRENT_WAREHOUSE"
        if self.get_parameter_by_field(key, PersonAdaptToCompany):
            return
        person_obj = Person(name=key, connection=self.conn)
        # XXX See ensure_current_branch comment: we have the same problem with
        # cnpj here.
        person_obj.addFacet(ICompany, cnpj='current_warehouse', 
                            connection=self.conn)
        self.set_schema(key, person_obj.id)

    def ensure_payment_destination(self):
        # Note that this method must always be called after
        # ensure_current_branch
        from stoq.domain.payment.destination import StoreDestination
        key = "DEFAULT_PAYMENT_DESTINATION"
        if self.get_parameter_by_field(key, StoreDestination):
            return
        branch = self.CURRENT_BRANCH
        pm = StoreDestination(description=_('Default Store Destination'),
                              branch=branch,
                              connection=self.conn)
        self.set_schema(key, pm.id)

    def ensure_payment_methods(self):
        from stoq.domain.payment.methods import PaymentMethod
        key = "METHOD_MONEY"
        if self.get_parameter_by_field(key, PaymentMethod):
            return
        destination = self.DEFAULT_PAYMENT_DESTINATION
        pm = PaymentMethod(connection=self.conn)
        for interface in [IMoneyPM, ICheckPM, IBillPM]:
            pm.addFacet(interface, connection=self.conn,
                        destination=destination)
        pm.addFacet(ICardPM, connection=self.conn)
        pm.addFacet(IFinancePM, connection=self.conn)
        self.set_schema('BASE_PAYMENT_METHOD', pm.id)
        self.set_schema(key, IMoneyPM(pm, connection=self.conn).id)

    def ensure_delivery_service(self):
        from stoq.domain.service import Service
        key = "DELIVERY_SERVICE"
        if self.get_parameter_by_field(key, Service):
            return
        service = Service(connection=self.conn)
        service.addFacet(ISellable, code='SD', price=0.0, description='Delivery',
                         connection=self.conn)
        self.set_schema(key, service.id)



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
# Ensuring everything
#


def ensure_system_parameters():
    print_msg("Creating default system parameters...", break_line=False)
    trans = new_transaction()
    param = sysparam(trans)
    param.set_defaults()
    trans.commit()
    print_msg('done')
