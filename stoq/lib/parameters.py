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
"""

import gettext

from stoqlib.exceptions import DatabaseInconsistency
from sqlobject import StringCol, BoolCol
from kiwi.python import namedAny, ClassInittableObject

from stoq.domain.base import Domain, AbstractModel
from stoq.domain.interfaces import (ISupplier, IBranch, ICompany, ISellable,
                                    IMoneyPM, ICheckPM, IBillPM, ICardPM,
                                    IFinancePM)
from stoq.lib.runtime import new_transaction, print_msg


_ = gettext.gettext


class ParameterDetails:
    def __init__(self, group, short_desc, long_desc):
        (self.group,
         self.short_desc,
         self.long_desc) = group, short_desc, long_desc


parameters_info = {
    'CURRENT_BRANCH': ParameterDetails(_('General'), _('Current Branch'),
                                       _('The current branch associated with '
                                         'the current system installation.')),
    'CURRENT_WAREHOUSE': ParameterDetails(_('General'), _('Current Warehouse'),
                                          _('The company\'s warehouse')),
    'DEFAULT_SALESPERSON_ROLE': ParameterDetails(_('Sales'),
                                                 _('Default Salesperson Role'),
                                                 _('Defines which of the '
                                                   'employee roles existent '
                                                   'in the system is the '
                                                   'salesperson role')),
    'SUGGESTED_SUPPLIER': ParameterDetails(_('Purchase'),
                                           _('Suggested Supplier'),
                                           _('The supplier suggested when we '
                                             'are adding a new product\'s '
                                             'supplier in the system')),
    'DEFAULT_BASE_CATEGORY': ParameterDetails(_('Purchase'),
                                              _('Default Base Sellable '
                                                'Category'),
                                              _('A default base sellable '
                                                'category which we always '
                                                'get as a suggestion when '
                                                'adding a new Sellable on '
                                                'the system')),
    'DEFAULT_PAYMENT_DESTINATION': ParameterDetails(_('Financial'),
                                                    _('Default Payment '
                                                      'Destination'),
                                                    _('A default payment '
                                                      'destination which will '
                                                      'be used for all the '
                                                      'created payments until '
                                                      'the user change the '
                                                      'destination of each '
                                                      'payment method.')),
    'BASE_PAYMENT_METHOD': ParameterDetails(_('Financial'),
                                            _('Base Payment Method'),
                                            _('The base payment method which '
                                              'can easily be converted to '
                                              'other methods like check and '
                                              'bill.')),
    'METHOD_MONEY': ParameterDetails(_('Financial'), _('Money Payment Method'),
                                     _('Definition of the money payment '
                                       'method. This parameter is not '
                                       'editable')),
    'DELIVERY_SERVICE': ParameterDetails(_('Sales'), _('Delivery Service'),
                                         _('The default delivery service '
                                           'in the system.')),
    'DEFAULT_GIFT_CERTIFICATE_TYPE': ParameterDetails(_('Sales'),
                                                      _('Default Gift '
                                                        'Certificate Type'),
                                                      _('The default gift '
                                                        'certificate type '
                                                        'used when canceling '
                                                        'sales and during '
                                                        'renegotiations.')),
    'USE_LOGIC_QUANTITY': ParameterDetails(_('Stock'), _('Use Logic Quantity'),
                                           _('An integer that defines if the '
                                             'company can work or not with '
                                             'logic quantities during stock '
                                             'operations. See StockItem '
                                             'documentation.')),
    'MAX_LATE_DAYS': ParameterDetails(_('Sales'), _('Client Maximum Late Days'),
                                      _('An integer that represents a maximum '
                                        'number of days which a certain client '
                                        'can have unpaid payments with normal '
                                        'status.')),
    'ACCEPT_ORDER_PRODUCTS': ParameterDetails(_('Sales'),
                                              _('Accept Order Products'),
                                              _('Can this company make sales '
                                                'for products that doesn\'t '
                                                'actually exist in the '
                                                'stock ? If this parameter '
                                                'is True we can order '
                                                'products.')),
    'CITY_SUGGESTED': ParameterDetails(_('General'), _('City Suggested'),
                                       _('When adding a new address for a '
                                         'certain person we will always '
                                         'suggest this city.')),
    'STATE_SUGGESTED': ParameterDetails(_('General'), _('State Suggested'),
                                        _('When adding a new address for a '
                                          'certain person we will always '
                                          'suggest this state.')),
    'COUNTRY_SUGGESTED': ParameterDetails(_('General'), _('Country Suggested'),
                                          _('When adding a new address for a '
                                            'certain person we will always '
                                            'suggest this country.')),
    'SELLABLE_PRICE_PRECISION': ParameterDetails(_('Sales'),
                                                 _('Sellable Price Precision'),
                                                 _('Precision for the price '
                                                   'attribute of a sellable '
                                                   'object.')),
    'STOCK_BALANCE_PRECISION': ParameterDetails(_('Stock'),
                                                _('Stock Balance Precision'),
                                                _('precision for product '
                                                  'stock balances.')),
    'PAYMENT_PRECISION': ParameterDetails(_('Financial'), _('Payment Precision'),
                                          _('Precision for payment values.')),
    'HAS_DELIVERY_MODE': ParameterDetails(_('Sales'), _('Has Delivery Mode'),
                                          _('Does this branch work with '
                                            'delivery service? If not, the '
                                            'delivery option will be disable '
                                            'on Point of Sales Application.')),
    'HAS_STOCK_MODE': ParameterDetails(_('Stock'), _('Has Stock Mode'),
                                       _('Does this branch work with storable '
                                         'items? If the answer is negative, '
                                         'we will disable stock operations in '
                                         'the system.')),
    'EDIT_SELLABLE_PRICE': ParameterDetails(_('Sales'),
                                            _('Edit Sellable Price'),
                                            _('Can we change the price '
                                              'attribute of a SellableItem '
                                              'object during a sale?')),
    'MAX_SEARCH_RESULTS': ParameterDetails(_('General'), _('Max Search Results'),
                                           _('The maximum number of results '
                                             'we must show after searching '
                                             'in any dialog.')),
    'MANDATORY_INTEREST_CHARGE': ParameterDetails(_('Sales'),
                                                  _('Mandatory Interest Charge'),
                                                  _('Once this paramter is set,'
                                                    ' the charge of monthly '
                                                    'interest will be mandatory '
                                                    'for every payment')),
    'COMPARISON_FLOAT_TOLERANCE': ParameterDetails(_('General'),
                                                   _('Comparison Float '
                                                     'Tolerance '),
                                                   _('This is useful when '
                                                     'performing comparison '
                                                     'between two float '
                                                     'numbers. If abs(numberA '
                                                     '- numberB) = This '
                                                     ' parameter value, the '
                                                     'two numbers can be '
                                                     'considerer equals')),
    'CONFIRM_SALES_ON_TILL': ParameterDetails(_('Sales'),
                                              _('Confirm Sales on Till'),
                                              _('Once this parameter is set, '
                                                'the sales confirmation are '
                                                'only made on till '
                                                'application and the fiscal '
                                                'coupon will be printed on '
                                                'that application instead of '
                                                'Point of Sales')),
    'SET_PAYMENT_METHODS_ON_TILL': ParameterDetails(_('Financial'),
                                                    _('Set Payment Methods on '
                                                      'Till'),
                                                    _('Do not show payment '
                                                      'method definitions step '
                                                      'on SaleWizard through '
                                                      'POS application if '
                                                      'CONFIRM_SALES_ON_TILL '
                                                      'is set. This step will '
                                                      'only be show on Till '
                                                      'application.')),
    'USE_PURCHASE_PREVIEW_PAYMENTS': ParameterDetails(_('Purchase'),
                                                      _('Use Purchase Preview '
                                                        'Payments'),
                                                      _('Generate preview '
                                                        'payments for new '
                                                        'purchases which are '
                                                        'not received yet. '
                                                        'Once the order is '
                                                        'received the preview '
                                                        'payments will be '
                                                        'also confirmed as '
                                                        'valid payments with '
                                                        'STATUS_TO_PAY')),
    'RETURN_MONEY_ON_SALES': ParameterDetails(_('Sales'),
                                              _('Return Money On Sales'),
                                              _('Once this parameter is set '
                                                'the salesperson can return '
                                                'money to clients when there '
                                                'is overpaid values in sales '
                                                'with gift certificates as '
                                                'payment method.')),
    'RECEIVE_PRODUCTS_WITHOUT_ORDER': ParameterDetails(_('Purchase'),
                                                       _('Receive Products '
                                                         'Without Order'),
                                                       _('Can we receive '
                                                         'products without '
                                                         'having a purchase '
                                                         'order created for '
                                                         'them ? If yes, the '
                                                         'first step of '
                                                         'ReceivalWizard '
                                                         'will accept going '
                                                         'to the second step '
                                                         'with no order '
                                                         'selected.')),
    }


#
# Infrastructure for system data
#

class ParameterData(Domain):
    """ Class to store system parameters.

    field_name = the name of the parameter we want to query on
    field_value = the current result(or value) of this parameter
    is_editable = if the item can't be edited through an editor.
    """
    field_name = StringCol(alternateID=True)
    field_value = StringCol()
    is_editable = BoolCol()

    def get_group(self):
        return parameters_info[self.field_name].group

    def get_short_description(self):
        return parameters_info[self.field_name].short_desc

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
                 ParameterAttr('USE_LOGIC_QUANTITY', bool, initial=True),
                 ParameterAttr('MAX_LATE_DAYS', int, initial=30),
                 ParameterAttr('SELLABLE_PRICE_PRECISION', int, initial=2),
                 ParameterAttr('HAS_STOCK_MODE', bool, initial=True),
                 ParameterAttr('HAS_DELIVERY_MODE', bool, initial=True),
                 ParameterAttr('STOCK_BALANCE_PRECISION', int, initial=2),
                 ParameterAttr('PAYMENT_PRECISION', int, initial=2),
                 ParameterAttr('EDIT_SELLABLE_PRICE', bool, initial=False),
                 ParameterAttr('ACCEPT_ORDER_PRODUCTS', bool, initial=True),
                 ParameterAttr('MAX_SEARCH_RESULTS', int, initial=600),
                 ParameterAttr('COMPARISON_FLOAT_TOLERANCE', float,
                               initial=0.02),
                 ParameterAttr('CITY_SUGGESTED', str, initial='Belo Horizonte'),
                 ParameterAttr('STATE_SUGGESTED', str, initial='MG'),
                 ParameterAttr('COUNTRY_SUGGESTED', str, initial='Brasil'),
                 ParameterAttr('CONFIRM_SALES_ON_TILL', bool, initial=False),
                 ParameterAttr('MANDATORY_INTEREST_CHARGE', bool, initial=False),
                 ParameterAttr('USE_PURCHASE_PREVIEW_PAYMENTS', bool, 
                               initial=True),
                 ParameterAttr('SET_PAYMENT_METHODS_ON_TILL', bool,
                               initial=False),
                 ParameterAttr('RETURN_MONEY_ON_SALES', bool, initial=True),
                 ParameterAttr('RECEIVE_PRODUCTS_WITHOUT_ORDER', bool, 
                               initial=True),

                 # Adding objects -- Note that all the object referred here must
                 # implements the IDescribable interface.
                 ParameterAttr('SUGGESTED_SUPPLIER', 
                               'person.PersonAdaptToSupplier'),
                 ParameterAttr('CURRENT_BRANCH', 
                               'person.PersonAdaptToBranch'),
                 ParameterAttr('DEFAULT_BASE_CATEGORY',
                               'sellable.BaseSellableCategory'),
                 ParameterAttr('DEFAULT_SALESPERSON_ROLE', 
                               'person.EmployeeRole'),
                 ParameterAttr('DEFAULT_PAYMENT_DESTINATION',
                               'payment.destination.PaymentDestination'),
                 ParameterAttr('BASE_PAYMENT_METHOD',
                               'payment.methods.PaymentMethod'),
                 ParameterAttr('METHOD_MONEY', 
                               'payment.methods.PMAdaptToMoneyPM'),
                 ParameterAttr('DELIVERY_SERVICE', 
                               'service.ServiceAdaptToSellable'),
                 ParameterAttr('DEFAULT_GIFT_CERTIFICATE_TYPE',
                               'giftcertificate.GiftCertificateType'),
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

    def set_schema(self, field_name, field_value, is_editable=True):
        ParameterData(connection=self.conn, field_name=field_name, 
                      field_value=field_value, is_editable=is_editable)

    def rebuild_cache_for(self, param_name):
        try:
            value = self._cache[param_name]
        except KeyError:
            return
        res = ParameterData.select(ParameterData.q.field_name == param_name,
                                   connection=self.conn)
        if not res.count():
                raise DatabaseInconsistency("Can't find a ParameterData"
                                            "object for the key %s"
                                            % param_name)
        elif res.count() > 1:
            raise DatabaseInconsistency("It is not possible have more than "
                                        "one ParameterData for the same "
                                        "key (%s)" % param_name)
        value_type = type(value)
        if not issubclass(value_type, AbstractModel):
            # XXX: workaround to works with boolean types:
            data = res[0].field_value
            if value_type is bool:
                data = int(data)
            self._cache[param_name] = value_type(data)
            return
        table = value_type
        obj_id = res[0].field_value
        self._cache[param_name] = table.get(obj_id, connection=self.conn)

    def rebuild_cache(self):
        map(self.rebuild_cache_for, self._cache.keys())

    def get_parameter_by_field(self, field_name, field_type):
        if isinstance(field_type, basestring):
            field_type = namedAny('stoq.domain.' + field_type)
        if self._cache.has_key(field_name):
            param = self._cache[field_name]
            if issubclass(field_type, AbstractModel):
                return field_type.get(param.id, connection=self.conn)
            return field_type(param)
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
            # XXX: workaround to works with boolean types:
            value = value.field_value
            if field_type is bool:
                value = int(value)
            param = field_type(value)
        self._cache[field_name] = param
        return param

    def set_defaults(self):
        constants = [c for c in self.constants if c.initial is not None]

        # Creating constants
        for obj in constants:
            if self.get_parameter_by_field(obj.key, obj.type):
                continue
            if obj.type is bool:
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
        self.ensure_default_salesperson_role()
        self.ensure_current_branch()
        self.ensure_current_warehouse()
        self.ensure_payment_destination()
        self.ensure_payment_methods()
        self.ensure_delivery_service()
        self.ensure_default_gift_certificate_type()

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

    def ensure_default_salesperson_role(self):
        from stoq.domain.person import EmployeeRole
        key = "DEFAULT_SALESPERSON_ROLE"
        if self.get_parameter_by_field(key, EmployeeRole):
            return
        role = EmployeeRole(name='Salesperson', 
                            connection=self.conn)
        self.set_schema(key, role.id, is_editable=False)

    def ensure_current_branch(self):
        from stoq.domain.person import (Person, PersonAdaptToBranch, Address,
                                        CityLocation)
        key = "CURRENT_BRANCH"
        if self.get_parameter_by_field(key, PersonAdaptToBranch):
            return

        person_obj = Person(name=key, connection=self.conn)
        city_location = CityLocation(city="Sao Carlos", state="SP",
                                     country="Brasil", connection=self.conn)
        main_address = Address(street="Orlando Damiano", number=2212,
                               district="Jd Macarengo", postal_code="11223344",
                               is_main_address=True, person=person_obj,
                               city_location=city_location,
                               connection=self.conn)
        # XXX Ok, I know. 'current_branch' is not a valid cnpj but as I don't know
        # what is the cnpj of this company I need to put something there because
        # this is a mandatory field. I think use a simple string could help user
        # to fix this field later.
        person_obj.addFacet(ICompany, cnpj=_('current_branch'), 
                            connection=self.conn)
        branch = person_obj.addFacet(IBranch, connection=self.conn)
        branch.manager = Person(connection=self.conn, name="Manager")
        self.set_schema(key, branch.id)

    def ensure_current_warehouse(self):
        from stoq.domain.person import Person, PersonAdaptToCompany
        key = "CURRENT_WAREHOUSE"
        if self.get_parameter_by_field(key, PersonAdaptToCompany):
            return
        person_obj = Person(name=key, connection=self.conn)
        # XXX See ensure_current_branch comment: we have the same problem with
        # cnpj here.
        person_obj.addFacet(ICompany, cnpj=_('current_warehouse'), 
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
        self.set_schema('BASE_PAYMENT_METHOD', pm.id, is_editable=False)
        self.set_schema(key, IMoneyPM(pm, connection=self.conn).id,
                        is_editable=False)

    def ensure_delivery_service(self):
        from stoq.domain.sellable import BaseSellableInfo
        from stoq.domain.service import Service
        key = "DELIVERY_SERVICE"
        if self.get_parameter_by_field(key, Service):
            return

        service = Service(connection=self.conn)

        sellable_info = BaseSellableInfo(connection=self.conn, 
                                         description=_('Delivery'), price=0.0)
        sellable = service.addFacet(ISellable, code='SD',
                                    base_sellable_info=sellable_info,
                                    connection=self.conn)
        self.set_schema(key, sellable.id)

    def ensure_default_gift_certificate_type(self):
        """Creates a initial gift certificate that will be tied with return
        values of sale cancelations.
        """
        from stoq.domain.sellable import BaseSellableInfo
        from stoq.domain.giftcertificate import GiftCertificateType
        key = "DEFAULT_GIFT_CERTIFICATE_TYPE"
        if self.get_parameter_by_field(key, GiftCertificateType):
            return
        description = _('General Gift Certificate')
        sellable_info = BaseSellableInfo(connection=self.conn, 
                                         description=description,
                                         price=0.0)
        certificate = GiftCertificateType(connection=self.conn,
                                          base_sellable_info=sellable_info)
        self.set_schema(key, certificate.id)


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


def get_parameter_details(field_name):
    """ Returns a ParameterDetails class for the given parameter name, or
    None if the name supplied isn't a valid parameter name.
    """
    try:
        return parameters_info[field_name]
    except KeyError:
        raise NameError("Does not exists no parameters "
                        "with name %s" % field_name)

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
