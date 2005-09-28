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
stoq/domain/interfaces.py:

    Interfaces definition for all domain classes.
"""

from twisted.python.components import (MetaInterface, Interface,
                                       _Nothing, CannotAdapt,
                                       _NoImplementor, getRegistry)


#
# Infrastructure
#


class Attribute:
    def __init__(self, __name__, __type__, __doc__=''):
        self.__name__=__name__
        self.__doc__=__doc__
        self.__type__ = __type__


class ConnMetaInterface(MetaInterface):
    def __call__(self, adaptable, default=_Nothing,
                 persist=None, registry=None, connection=None):
        """
        Try to adapt `adaptable' to self; return `default' if it was passed, otherwise
        raise L{CannotAdapt}.
        """
        adapter = default
        registry = getRegistry(registry)
        # should this be `implements' of some kind?
        if (persist is None or persist) and hasattr(adaptable, 'getComponent'):
            adapter = adaptable.getComponent(self, registry,
                                             default=_NoImplementor,
                                             connection=connection)
        else:
            adapter = registry.getAdapter(adaptable, self,
                                          _NoImplementor,
                                          persist=persist)
        if adapter is _NoImplementor:
            if hasattr(self, '__adapt__'):
                adapter = self.__adapt__.im_func(adaptable, default)
            else:
                adapter = default

        if adapter is _Nothing:
            raise CannotAdapt("%s cannot be adapted to %s." %
                              (adaptable, self))
        return adapter

class ConnInterface(Interface):
    __metaclass__ = ConnMetaInterface
    

    
#
# ConnInterfaces
#



class IContainer(ConnInterface):
    """An objects that holds other objects or items"""


    def add_item(item):
        """Add a persistent or non-persistent item associated with this
        model."""

    def get_items():
        """Get all the items in the container. The result value could be a
        simple python list or an instance which maps to SQL statement.  """

    def remove_items(item):
        """Remove from the list or database the item desired."""


class ISellable(ConnInterface):
    """ Represents the sellable information of a certain item such a product
    or a service. Note that sellable is not actually a concrete item but
    only its reference as a sellable. Concrete items are defined by
    IContainer routines."""

    state = Attribute('state', 
                      'enum',
                      'state the sellable is in')
    price = Attribute('price',
                      'float',
                      'price of sellable')
    description = Attribute('description',
                            'str',
                            'full description of sallable')
    category = Attribute('category', 
                         'SellableCategory', 
                         'a reference to category table')
    markup = Attribute('markup',
                       'float',
                       '((cost/price)-1)*100')
    cost = Attribute('cost',
                     'float',
                     'final cost of sellable')
    max_discount = Attribute('max_discount',
                             'float', 
                             'maximum discount allowed')
    comission = Attribute('comission',
                          'float', 
                          'comission to pay after selling this sellable')

    # If the sellable is on sale, here we have settings for that
    on_sale_price = Attribute('on_sale_price', 
                              'float',
                              'A special price used when we have a '
                              '"on sale" state')
    # Define here the period that this sellabe will be on sale
    on_sale_start_date = Attribute('on_sale_start_date',
                                   'datetime')
    on_sale_end_date = Attribute('on_sale_end_date',
                                 'datetime')

    def can_be_sold():
        pass

    def set_sold():
        pass

    def get_price():
        pass

    def add_sellable_item(sale, quantity, price):
        """Adds a new SellableItem instance for this sellable object"""


class IStorable(ConnInterface):
    """Storable documentation for a certain product or a sellable item. 
    Each storable can have references to many concrete items which will
    be defined by IContainer routines."""

    def fill_stocks(conn):
        """Fill the stock references of the current product to point to 
        stock correct information in all the branches"""

    def increase_stock(quantity, branch=None):
        """When receiving a product, update the stock reference for this new
        item. If no branch company is supplied, update all branches."""

    def increase_logic_stock(quantity, branch=None):
        """When receiving a product, update the stock logic quantity
        reference for this new item. If no branch company is supplied, 
        update all branches."""

    def decrease_stock(quantity, branch=None):
        """When selling a product, update the stock reference for the sold
        item. If no branch company is supplied, update all branches."""

    def decrease_logic_stock(quantity, branch=None):
        """When selling a product, update the stock logic reference for the sold
        item. If no branch company is supplied, update all branches."""

    def get_full_balance(branch=None):
        """Return the stock balance for the current product. If a branch
        company is supplied, get the stock balance for this branch, 
        otherwise, get the stock balance for all the branches. 
        We get also the sum of logic_quantity attributes"""

    def get_logic_balance(branch=None):
        """Return the stock logic balance for the current product. If a branch
        company is supplied, get the stock balance for this branch, 
        otherwise, get the stock balance for all the branches."""

    def get_average_stock_price():
        """Average stock price is: SUM(total_cost attribute, StockItem
        object) of all the branches DIVIDED BY SUM(quantity atribute,
        StockReference object)
        """
    def ensure_qty_requested(quantity, branch):
        """Check if the quantity requested in a sale is valid and update the
        stock of the sellable item"""
        
        
class IIndividual(ConnInterface):
    """Being or characteristic of a single person, concerning one
    person exclusively"""

    cpf = Attribute('cpf', 
                    'str',
                    'A Brazilian government register number which allow to '
                    'store credit informations')
    rg_number = Attribute('rg_number',
                          'str',
                          'A Brazilian government register which identify an '
                          'individual')
    birth_location = Attribute('birth_location',
                               'integer',
                               'An object which has city, state and country')
    birth_date = Attribute('birth_date', 
                           'datetime',
                           'The date which this individual was born')
    occupation = Attribute('occupation', 
                           'str',
                           'The current job of this individual')
    marital_status = Attribute('marital_status',
                               'enum',
                               'single, married, divorced, widowed')
    spouse = Attribute('spouse', 
                       'Individual',
                       'An individual\'s partner in marriage - also a '
                       'reference to another individual')
    father_name = Attribute('father_name',
                            'str',
                            'The father of this individual')
    mother_name = Attribute('mother_name', 
                            'str',
                            'The mother of this individual')
    rg_expedition_date = Attribute('rg_expedition_date', 
                                   'datetime',
                                   'Expedition date for the Brazilian '
                                   'document')
    rg_expedition_local = Attribute('rg_expedition_local', 
                                    'str',
                                    'The local which the Brazilian was made')
    gender = Attribute('gender', 
                       'enum',
                       'gender_male, gender_female')


class ICompany(ConnInterface):
    """An institution created to conduct business"""

    cnpj = Attribute('cnpj', 
                     'str',
                     'A Brazilian government register number for companies')
    fancy_name = Attribute('fancy_name', 
                           'str',
                           'The secondary company name')
    state_registry = Attribute('state_registry', 
                               'str',
                               'A Brazilian register number associated with '
                               'a certain state')


class IClient(ConnInterface):
    """An individual or a company who pays for goods or services"""

    status = Attribute('status',
                       'enum',
                       'ok, indebted, insolvent, inactive')
    days_late = Attribute('days_late', 
                          'int',
                          'How many days is this client indebted')


class ISupplier(ConnInterface):
    """A company or an individual that produces, provides, or furnishes 
    an item or service"""

    product_desc = Attribute('product_desc',
                             'str',
                             'A short description telling which products '
                             'this supplier produces')
    status = Attribute('status', 
                       'enum',
                       'active, inactive, blocked')


class IEmployee(ConnInterface):
    """An individual who performs work for an employer under a verbal 
    or written understanding where the employer gives direction as to 
    what tasks are done"""

    admission_date = Attribute('admission_date',
                               'datetime')
    expire_vacation = Attribute('expire_vacation',
                                'datetime')
    salary = Attribute('salary',
                       'float')
    status = Attribute('status',
                       'enum',
                       'normal, away, vacation, off')
    registry_number = Attribute('registry_number',
                                'str')
    education_level = Attribute('education_level',
                                'str')
    dependent_person_number = Attribute('dependent_person_number',
                                        'integer')
    
    # This is Brazil-specif information
    workpermit_data = Attribute('workpermit_data',
                                'WorkPermitData')
    military_data = Attribute('military_data',
                              'MilitaryData')
    voter_data = Attribute('voter_data',
                           'VoterData')
    bank_account  = Attribute('bank_account',
                              'BankAccount')
    position = Attribute('position',
                         'EmployeePosition',
                         'A reference to an employee position object')


class IUser(ConnInterface):
    """An employee which have access to one or more Stoq applications"""

    username = Attribute('username',
                         'str')
    profile = Attribute('profile',
                        'UserProfile',
                        'A profile represents a colection of information '
                        'which represents what this user can do in the '
                        'system')
    password = Attribute('password', 
                         'str')


class IBranch(ConnInterface):
    """An administrative division of some larger or more complex
    organization"""

    manager = Attribute('manager', 
                        'Employee',
                        'An employee which is in charge of this branch')
    
class ISalesPerson(ConnInterface):
    """An employee in charge of make sales"""

    comission = Attribute('commission', 
                          'float', 
                          'The percentege of comission the company must pay '
                          'for this salesman')
    comission_type = Attribute('comission_type', 
                               'int',
                               'A rule used to calculate the amount of '
                               'comission. This is a reference to another '
                               'object')


class IInPayment(ConnInterface):
    """ Interface specification for InPayments. """

    def receive(value=None, paid_date=None):
        """ Confirm the payment. """


class IOutPayment(ConnInterface):
    """ Interface specification for OutPayments. """

    def pay(value=None, paid_date=None):
        """ Confirm the payment."""


class IPaymentGroup(ConnInterface):
    """ Interface specification for PaymentGroups. """

    status = Attribute('status',
                       'int',
                       'The status of the payment group. ')
    open_date = Attribute('open_date',
                          'datetime',
                          'The open date of the payment group.')
    close_date = Attribute('close_date',
                           'datetime',
                           'The close date of the payment group.')
    notes = Attribute('notes',
                      'str',
                      'Extra notes for the payment group.')
    payments = Attribute('payments',
                         'list',
                         'A list of payments associated to this payment '
                         'group') 
    thirdparty = Attribute('thirdparty',
                           'Person',
                           'The thirdparty associated to this payment group.')

class IDelivery(ConnInterface):
    """ Specification of a Delivery interface for a sellable. """

    address = Attribute('address',
			'str',
			'The delivery address.')
