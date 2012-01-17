# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source
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
""" Parameters and system data for applications"""

from decimal import Decimal
import os

from kiwi.argcheck import argcheck
from kiwi.datatypes import ValidationError
from kiwi.log import Logger
from kiwi.python import namedAny, ClassInittableObject
from stoqdrivers.enum import TaxType

import stoqlib
from stoqlib.database.runtime import new_transaction
from stoqlib.domain.parameter import ParameterData
from stoqlib.domain.interfaces import ISupplier, IBranch
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.imageutils import ImageHelper
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import (validate_int,
                                    validate_decimal,
                                    validate_directory,
                                    validate_area_code,
                                    validate_percentage,
                                    validate_state)
from stoqlib.lib.barcode import BarcodeInfo

_ = stoqlib_gettext
log = Logger('stoqlib.parameters')


class DirectoryParameter(object):
    def __init__(self, path):
        self.path = path


class ParameterDetails(object):
    def __init__(self, key, group, short_desc, long_desc, type,
                 initial=None, options=None, range=None,
                 multiline=False, validator=None, onupgrade=None):
        self.key = key
        self.group = group
        self.short_desc = short_desc
        self.long_desc = long_desc
        self.type = type
        self.initial = initial
        self.options = options
        self.range = range
        self.multiline = multiline
        self.validator = validator
        if onupgrade is None:
            onupgrade = initial
        self.onupgrade = onupgrade

    #
    #  Public API
    #

    def get_parameter_type(self):
        if isinstance(self.type, basestring):
            return namedAny('stoqlib.domain.' + self.type)
        else:
            return self.type

    def get_parameter_validator(self):
        return self.validator or self._get_generic_parameter_validator()

    #
    #  Staticmethods
    #

    @staticmethod
    def validate_int(value):
        if not validate_int(value):
            return ValidationError(_("This parameter only accepts "
                                     "integer values."))

    @staticmethod
    def validate_decimal(value):
        if not validate_decimal(value):
            return ValidationError(_("This parameter only accepts "
                                     "decimal values."))

    @staticmethod
    def validate_directory(path):
        if not validate_directory(path):
            return ValidationError(_("'%s is not a valid path.'") % path)

    @staticmethod
    def validate_area_code(code):
        if not validate_area_code(code):
            return ValidationError(_("'%s' is not a valid area code.\n"
                                     "Valid area codes are on 10-99 range.")
                                   % code)

    @staticmethod
    def validate_percentage(value):
        if not validate_percentage(value):
            return ValidationError(_("'%s' is not a valid percentage.")
                                   % value)

    @staticmethod
    def validate_state(state):
        if not validate_state(state):
            return ValidationError(_("'%s' is not a valid state.")
                                   % state)

    #
    #  Private API
    #

    def _get_generic_parameter_validator(self):
        p_type = self.get_parameter_type()

        if issubclass(p_type, int):
            return ParameterDetails.validate_int
        elif issubclass(p_type, Decimal):
            return ParameterDetails.validate_decimal
        elif issubclass(p_type, DirectoryParameter):
            return ParameterDetails.validate_directory

_details = [
    ParameterDetails(
        'EDIT_CODE_PRODUCT',
        ('Products'),
        ('Disable edit code products'),
        ('Disable edit code products on purchase application'),
        bool, initial=False),

    ParameterDetails(
        'MAIN_COMPANY',
        _('General'),
        _('Primary company'),
        _('The primary company which is the owner of all other '
          'branch companies'),
        'person.PersonAdaptToBranch'),

    ParameterDetails(
        'CUSTOM_LOGO_FOR_REPORTS',
        _('General'),
        _('Custom logotype for reports'),
        _('Defines a custom logo for all the reports generated by Stoq. '
          'The recommended image dimension is 171x59 (pixels), if needed, '
          'the image will be resized. In order to use the default logotype '
          'leave this field blank'), ImageHelper, initial=''),

    ParameterDetails(
        'DISABLE_COOKIES',
        _('General'),
        _('Disable cookies'),
        _('Disable the ability to use cookies in order to automatic log in '
          'the system. If so, all the users will have to provide the password '
          'everytime they log in. Requires restart to take effect.'),
        bool, initial=False),

    ParameterDetails(
        'DEFAULT_SALESPERSON_ROLE',
        _('Sales'),
        _('Default salesperson role'),
        _('Defines which of the employee roles existent in the system is the '
          'salesperson role'),
        'person.EmployeeRole'),

    # FIXME: s/SUGGESTED/DEFAULT/
    ParameterDetails(
        'SUGGESTED_SUPPLIER',
        _('Purchase'),
        _('Suggested supplier'),
        _('The supplier suggested when we are adding a new product in the '
          'system'),
        'person.PersonAdaptToSupplier'),

    ParameterDetails(
        'SUGGESTED_UNIT',
        _('Purchase'),
        _('Suggested unit'),
        _('The unit suggested when we are adding a new product in the '
          'system'),
        'sellable.SellableUnit'),

    ParameterDetails(
        'DEFAULT_BASE_CATEGORY',
        _('Purchase'),
        _('Default base sellable category'),
        _('A default base sellable category which we always get as a '
          'suggestion when adding a new Sellable on the system'),
        'sellable.SellableCategory'),

    ParameterDetails(
        'ALLOW_OUTDATED_OPERATIONS',
        _('General'),
        _('Allow outdated operations'),
        _('Allows the inclusion of purchases and payments done previously than the '
          'current date.'),
        bool, initial=False),

    ParameterDetails(
        'DELIVERY_SERVICE',
        _('Sales'),
        _('Delivery service'),
        _('The default delivery service in the system.'),
        'service.Service'),

    ParameterDetails(
        'USE_LOGIC_QUANTITY',
        _('Stock'),
        _('Use logic quantity'),
        _('An integer that defines if the company can work or not with '
          'logic quantities during stock operations. See StockItem '
          'documentation.'),
          bool, initial=True),

    # XXX This parameter is POS-specific. How to deal with that
    # in a better way?
    ParameterDetails(
        'POS_FULL_SCREEN',
        _('Sales'),
        _('Show POS application in Fullscreen'),
        _('Once this parameter is set the Point of Sale application '
          'will be showed as full screen'),
        bool, initial=False),

    ParameterDetails(
        'POS_SEPARATE_CASHIER',
        _('Sales'),
        _('Exclude cashier operations in Point of Sale'),
        _('If you have a computer that will be a Point of Sales and have a '
          'fiscal printer connected, set this False, so the Till menu will '
          'appear on POS. If you prefer to separate the Till menu from POS '
          'set this True.'),
        bool, initial=False),

    ParameterDetails(
        'ENABLE_PAULISTA_INVOICE',
        _('Sales'),
        _('Enable paulista invoice'),
        _('Once this parameter is set, we will be able to join to the '
          'Sao Paulo state program of fiscal commitment.'),
        bool, initial=False),

    ParameterDetails(
        'CITY_SUGGESTED',
        _('General'),
        _('Default city'),
        _('When adding a new address for a certain person we will always '
          'suggest this city.'),
        str, initial='Sao Carlos'),

    ParameterDetails(
        'STATE_SUGGESTED',
        _('General'),
        _('Default state'),
        _('When adding a new address for a certain person we will always '
          'suggest this state.'),
        str, initial='SP', validator=ParameterDetails.validate_state),

    ParameterDetails(
        'COUNTRY_SUGGESTED',
        _('General'),
        _('Default country'),
        _('When adding a new address for a certain person we will always '
          'suggest this country.'),
        str, initial='Brazil'),

    ParameterDetails(
        'HAS_DELIVERY_MODE',
        _('Sales'),
        _('Has delivery mode'),
        _('Does this branch work with delivery service? If not, the '
          'delivery option will be disable on Point of Sales Application.'),
        bool, initial=True),

    ParameterDetails(
        'SHOW_COST_COLUMN_IN_SALES',
        _('Sales'),
        _('Show cost column in sales'),
        _('should the cost column be displayed when creating a new sale quote.'),
        bool, initial=False),

    ParameterDetails(
        'MAX_SEARCH_RESULTS',
        _('General'),
        _('Max search results'),
        _('The maximum number of results we must show after searching '
          'in any dialog.'),
        int, initial=600),

    ParameterDetails(
        'CONFIRM_SALES_ON_TILL',
        _('Sales'),
        _('Confirm sales in Till'),
        _('Once this parameter is set, the sales confirmation are only made '
          'on till application and the fiscal coupon will be printed on '
          'that application instead of Point of Sales'),
        bool, initial=False),

    ParameterDetails(
        'ACCEPT_CHANGE_SALESPERSON',
        _('Sales'),
        _('Change salesperson'),
        _('Once this parameter is set to true, the user will be '
          'able to change the salesperson of an opened '
          'order on sale checkout dialog'),
        bool, initial=False),

    ParameterDetails(
        'RETURN_MONEY_ON_SALES',
        _('Sales'),
        _('Return money on sales'),
        _('Once this parameter is set the salesperson can return '
          'money to clients when there is overpaid values in sales '
          'with gift certificates as payment method.'),
        bool, initial=True),

    ParameterDetails(
        'MAX_SALE_DISCOUNT',
        _('Sales'),
        _('Max discount for sales'),
        _('The max discount for salesperson in a sale'),
        Decimal, initial=5,
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        'SALE_PAY_COMMISSION_WHEN_CONFIRMED',
        _('Sales'),
        _('Commission Payment At Sale Confirmation'),
        _('Define whether the commission is paid when a sale is confirmed. '
          'If True pay the commission when a sale is confirmed, '
          'if False, pay a relative commission for each commission when '
          'the sales payment is paid.'),
        bool, initial=False),

    ParameterDetails(
        'DEFAULT_OPERATION_NATURE',
        _('Sales'),
        _('Default operation nature'),
        _('When adding a new sale quote, we will always suggest '
          'this operation nature'),
        str, initial=_('Sale')),

    ParameterDetails(
        'ASK_SALES_CFOP',
        _('Sales'),
        _('Ask for Sale Order C.F.O.P.'),
        _('Once this parameter is set to True we will ask for the C.F.O.P. '
          'when creating new sale orders'),
        bool, initial=False),

    ParameterDetails(
        'DEFAULT_SALES_CFOP',
        _('Sales'),
        _('Default Sales C.F.O.P.'),
        _('Default C.F.O.P. (Fiscal Code of Operations) used when generating '
          'fiscal book entries.'),
        'fiscal.CfopData'),

    ParameterDetails(
        'DEFAULT_RETURN_SALES_CFOP',
        _('Sales'),
        _('Default Return Sales C.F.O.P.'),
        _('Default C.F.O.P. (Fiscal Code of Operations) used when returning '
          'sale orders '),
        'fiscal.CfopData'),

    ParameterDetails(
        'DEFAULT_RECEIVING_CFOP',
        _('Purchase'),
        _('Default Receiving C.F.O.P.'),
        _('Default C.F.O.P. (Fiscal Code of Operations) used when receiving '
          'products in the stock application.'),
        'fiscal.CfopData'),

    ParameterDetails(
        'DEFAULT_STOCK_DECREASE_CFOP',
        _('Stock'),
        _('Default C.F.O.P. for Stock Decreases'),
        _('Default C.F.O.P. (Fiscal Code of Operations) used when performing a '
          'manual stock decrease.'),
        'fiscal.CfopData'),

    ParameterDetails(
        'ICMS_TAX',
        _('Sales'),
        _('Default ICMS tax'),
        _('Default ICMS to be applied on all the products of a sale. ') + ' ' +
        _('This is a percentage value and must be between 0 and 100.') + ' ' +
        _('E.g: 18, which means 18% of tax.'),
        Decimal, initial=18,
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        'ISS_TAX',
        _('Sales'),
        _('Default ISS tax'),
        _('Default ISS to be applied on all the services of a sale. ') + ' ' +
        _('This is a percentage value and must be between 0 and 100.') + ' ' +
        _('E.g: 12, which means 12% of tax.'),
        Decimal, initial=18,
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        'SUBSTITUTION_TAX',
        _('Sales'),
        _('Default Substitution tax'),
        _('The tax applied on all sale products with substitution tax type.') +
        ' ' +
        _('This is a percentage value and must be between 0 and 100.') + ' ' +
        _('E.g: 16, which means 16% of tax.'),
        Decimal, initial=18,
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        'DEFAULT_AREA_CODE',
        _('General'),
        _('Default area code'),
        _('This is the default area code which will be used when '
          'registering new clients, users and more to the system'),
        int, initial=16,
        validator=ParameterDetails.validate_area_code),

    ParameterDetails(
        'DEFAULT_PRODUCT_TAX_CONSTANT',
        _('Sales'),
        _('Default tax constant for products'),
        _('This is the default tax constant which will be used '
          'when adding new products to the system'),
        'sellable.SellableTaxConstant'),

    ParameterDetails(
        'CAT52_DEST_DIR',
        _('General'),
        _('Cat 52 destination directory'),
        _('Where the file generated after a Z-reduction should be saved.'),
        DirectoryParameter, initial='~/.stoq/cat52'),

    ParameterDetails(
        'COST_PRECISION_DIGITS',
        _('General'),
        _('Number of digits to use for product cost'),
        _('Set this parameter accordingly to the number of digits of the '
          'products you purchase'),
        int, initial=2, range=[2, 8]),

    ParameterDetails(
        'SCALE_BARCODE_FORMAT',
        _('Sales'),
        _('Scale barcode format'),
        _('Format used by the barcode printed by the scale. This format always'
          ' starts with 2 followed by 4,5 or 6 digits product code and by a 5'
          ' digit weight or a 6 digit price. Check or scale documentation and'
          ' configuration to see the best option.'),
        int, initial=0,
        options=BarcodeInfo.options),

    ParameterDetails(
        'NFE_SERIAL_NUMBER',
        _('NF-e'),
        _('Fiscal document serial number'),
        _('Fiscal document serial number. Fill with 0 if the NF-e have no '
          'series. This parameter only has effect if the nfe plugin is enabled.'),
        int, initial=1),

    ParameterDetails(
        'NFE_DANFE_ORIENTATION',
        _('NF-e'),
        _('Danfe printing orientation'),
        _('Orientation to use for printing danfe. Portrait or Landscape'),
        int, initial=0,
        options={0: _('Portrait'),
                 1: _('Landscape')}),

    ParameterDetails(
        'NFE_FISCO_INFORMATION',
        _('NF-e'),
        _('Additional Information for the Fisco'),
        _('Additional information to add to the NF-e for the Fisco'), str,
        initial=('Documento emitido por ME ou EPP optante pelo SIMPLES '
                 'NACIONAL. Não gera Direito a Crédito Fiscal de ICMS e de '
                 'ISS. Conforme Lei Complementar 123 de 14/12/2006.'),
        multiline=True),

    ParameterDetails(
        'BANKS_ACCOUNT',
        _('Accounts'),
        _('Parent bank account'),
        _('Newly created bank accounts will be placed under this account.'),
        'account.Account'),

    ParameterDetails(
        'TILLS_ACCOUNT',
        _('Accounts'),
        _('Parent till account'),
        _('Till account transfers will be placed under this account'),
        'account.Account'),

    ParameterDetails(
        'IMBALANCE_ACCOUNT',
        _('Accounts'),
        _('Imbalance account'),
        _('Account used for unbalanced transactions'),
        'account.Account'),

    ParameterDetails(
        'DEMO_MODE',
        _('General'),
        _('Demonstration mode'),
        _('If Stoq is used in a demonstration mode'),
        bool, initial=False),

    ParameterDetails(
        'BLOCK_INCOMPLETE_PURCHASE_PAYMENTS',
        _('Payments'),
        _('Block incomplete purchase payments'),
        _('Do not allow confirming a account payable if the purchase is not '
          'completely received.'),
        bool, initial=False),

    # This parameter is tricky, we want to ask the user to fill it in when
    # upgrading from a previous version, but not if the user installed Stoq
    # from scratch. Some of the hacks involved with having 3 boolean values
    # ("", True, False) can be removed if we always allow None and treat it like
    # and unset value in the database.
    ParameterDetails(
        'ONLINE_SERVICES',
        _('General'),
        _('Online services'),
        _('If online services such as upgrade notifications, automatic crash reports '
          'should be enabled.'),
        bool, initial=True, onupgrade=''),

    ParameterDetails(
        'BILL_INSTRUCTIONS',
        _('Sales'),
        _('Bill instructions '),
        # Translators: do not translate $DATE
        _('When printing bills, include the first 3 lines of these on '
          'the bill itself. This usually includes instructions on how '
          'to pay the bill and the validity and the terms. $DATE will be'
          'replaced with the due date of the bill'),
        str, multiline=True, initial=""),

]


class ParameterAccess(ClassInittableObject):
    """A mechanism to tie specific instances to constants that can be
    made available cross-application. This class has a special hook that
    allows the values to be looked up on-the-fly and cached.

    Usage:

    >>> from stoqlib.lib.parameters import sysparam
    >>> from stoqlib.database.runtime import get_connection
    >>> conn = get_connection()
    >>> parameter = sysparam(conn).parameter_name
    """

    _cache = {}

    @classmethod
    def __class_init__(cls, namespace):
        for detail in _details:
            getter = lambda self, n=detail.key, v=detail.type: (
                self.get_parameter_by_field(n, v))
            setter = lambda self, value, n=detail.key: (
                self._set_schema(n, value))
            prop = property(getter, setter)
            setattr(cls, detail.key, prop)

    def __init__(self, conn):
        ClassInittableObject.__init__(self)
        self.conn = conn

    def _remove_unused_parameters(self):
        """Remove any  parameter found in ParameterData table which is not
        used any longer.
        """
        detail_keys = [detail.key for detail in _details]
        for param in ParameterData.select(connection=self.conn):
            if param.field_name not in detail_keys:
                ParameterData.delete(param.id, connection=self.conn)

    def _set_schema(self, field_name, field_value, is_editable=True):
        if field_value is not None:
            field_value = str(field_value)

        data = ParameterData.selectOneBy(connection=self.conn,
                                         field_name=field_name)
        if data is None:
            ParameterData(connection=self.conn,
                          field_name=field_name,
                          field_value=field_value,
                          is_editable=is_editable)
        else:
            data.field_value = field_value

    def _set_default_value(self, detail, initial):
        if initial is None:
            return

        value = initial
        if detail.type is bool:
            if value != "":
                value = int(initial)
        self._set_schema(detail.key, value)

    def _create_default_values(self):
        # Create default values for parameters that take objects
        self._create_default_sales_cfop()
        self._create_default_return_sales_cfop()
        self._create_default_receiving_cfop()
        self._create_default_stock_decrease_cfop()
        self._create_suggested_supplier()
        self._create_suggested_unit()
        self._create_default_base_category()
        self._create_default_salesperson_role()
        self._create_main_company()
        self._create_delivery_service()
        self._create_product_tax_constant()

    def _create_suggested_supplier(self):
        key = "SUGGESTED_SUPPLIER"
        from stoqlib.domain.person import Person
        if self.get_parameter_by_field(key, Person.getAdapterClass(ISupplier)):
            return
        self._set_schema(key, None)

    def _create_suggested_unit(self):
        key = "SUGGESTED_UNIT"
        from stoqlib.domain.sellable import SellableUnit
        if self.get_parameter_by_field(key, SellableUnit):
            return
        self._set_schema(key, None)

    def _create_default_base_category(self):
        from stoqlib.domain.sellable import SellableCategory
        key = "DEFAULT_BASE_CATEGORY"
        if self.get_parameter_by_field(key, SellableCategory):
            return
        base_category = SellableCategory(description=key,
                                         connection=self.conn)
        self._set_schema(key, base_category.id)

    def _create_default_salesperson_role(self):
        from stoqlib.domain.person import EmployeeRole
        key = "DEFAULT_SALESPERSON_ROLE"
        if self.get_parameter_by_field(key, EmployeeRole):
            return
        role = EmployeeRole(name=_('Salesperson'),
                            connection=self.conn)
        self._set_schema(key, role.id, is_editable=False)

    def _create_main_company(self):
        from stoqlib.domain.person import Person
        key = "MAIN_COMPANY"
        if self.get_parameter_by_field(key, Person.getAdapterClass(IBranch)):
            return
        self._set_schema(key, None)

    def _create_delivery_service(self):
        from stoqlib.domain.service import Service
        key = "DELIVERY_SERVICE"
        if self.get_parameter_by_field(key, Service):
            return

        self.create_delivery_service()

    def _create_cfop(self, key, description, code):
        from stoqlib.domain.fiscal import CfopData
        if self.get_parameter_by_field(key, CfopData):
            return
        data = CfopData.selectOneBy(code=code, connection=self.conn)
        if not data:
            data = CfopData(code=code, description=description,
                            connection=self.conn)
        self._set_schema(key, data.id)

    def _create_default_return_sales_cfop(self):
        self._create_cfop("DEFAULT_RETURN_SALES_CFOP",
                          "Devolucao",
                          "5.202")

    def _create_default_sales_cfop(self):
        self._create_cfop("DEFAULT_SALES_CFOP",
                          "Venda de Mercadoria Adquirida",
                          "5.102")

    def _create_default_receiving_cfop(self):
        self._create_cfop("DEFAULT_RECEIVING_CFOP",
                          "Compra para Comercializacao",
                          "1.102")

    def _create_default_stock_decrease_cfop(self):
        self._create_cfop("DEFAULT_STOCK_DECREASE_CFOP",
                          "Outra saída de mercadoria ou "
                          "prestação de serviço não especificado",
                          "5.949")

    def _create_product_tax_constant(self):
        from stoqlib.domain.sellable import SellableTaxConstant
        key = "DEFAULT_PRODUCT_TAX_CONSTANT"
        if self.get_parameter_by_field(key, SellableTaxConstant):
            return

        tax_constant = SellableTaxConstant.get_by_type(TaxType.NONE, self.conn)
        self._set_schema(key, tax_constant.id)

    #
    # Public API
    #

    @argcheck(str, object)
    def update_parameter(self, parameter_name, value):
        if parameter_name in ['DEMO_MODE']:
            raise AssertionError
        param = get_parameter_by_field(parameter_name, self.conn)
        param.field_value = str(value)
        self.rebuild_cache_for(parameter_name)

    def rebuild_cache_for(self, param_name):
        from stoqlib.domain.base import AbstractModel
        try:
            value = self._cache[param_name]
        except KeyError:
            return

        param = get_parameter_by_field(param_name, self.conn)
        value_type = type(value)
        if not issubclass(value_type, AbstractModel):
            # XXX: workaround to works with boolean types:
            data = param.field_value
            if value_type is bool:
                data = int(data)
            self._cache[param_name] = value_type(data)
            return
        table = value_type
        obj_id = param.field_value
        self._cache[param_name] = table.get(obj_id, connection=self.conn)

    def clear_cache(self):
        log.info("Clearing cache")
        ParameterAccess._cache = {}

    def get_parameter_constant(self, field_name):
        for detail in _details:
            if detail.key == field_name:
                return detail
        else:
            raise KeyError("No such a parameter: %s" % (field_name, ))

    def get_parameter_type(self, field_name):
        detail = self.get_parameter_constant(field_name)

        if isinstance(detail.type, basestring):
            return namedAny('stoqlib.domain.' + detail.type)
        else:
            return detail.type

    def get_parameter_by_field(self, field_name, field_type):
        from stoqlib.domain.base import AbstractModel
        if isinstance(field_type, basestring):
            field_type = namedAny('stoqlib.domain.' + field_type)
        if field_name in self._cache:
            param = self._cache[field_name]
            if issubclass(field_type, AbstractModel):
                return field_type.get(param.id, connection=self.conn)
            elif issubclass(field_type, (ImageHelper, DirectoryParameter)):
                return param
            else:
                return field_type(param)
        value = ParameterData.selectOneBy(field_name=field_name,
                                          connection=self.conn)
        if value is None:
            return
        if issubclass(field_type, AbstractModel):
            if value.field_value == '' or value.field_value is None:
                return
            param = field_type.get(value.field_value, connection=self.conn)
        else:
            # XXX: workaround to works with boolean types:
            value = value.field_value
            if field_type is bool:
                if value == 'True':
                    param = True
                elif value == 'False':
                    param = False
                # This is a pre-1.0 migration specific hack
                elif value == "":
                    return None
                else:
                    param = bool(int(value))
            else:
                param = field_type(value)
        self._cache[field_name] = param
        return param

    def update(self):
        """Called when migrating the database"""
        self._remove_unused_parameters()
        for detail in _details:
            param = self.get_parameter_by_field(detail.key, detail.type)
            if param is not None:
                continue
            self._set_default_value(detail, detail.onupgrade)
        self._create_default_values()

    def set_defaults(self):
        """Called when creating a new database"""
        self._remove_unused_parameters()
        for detail in _details:
            self._set_default_value(detail, detail.initial)
        self._create_default_values()

    def create_delivery_service(self):
        from stoqlib.domain.sellable import (Sellable,
                                             SellableTaxConstant)
        from stoqlib.domain.service import Service
        key = "DELIVERY_SERVICE"
        tax_constant = SellableTaxConstant.get_by_type(TaxType.SERVICE, self.conn)
        sellable = Sellable(tax_constant=tax_constant,
                            description=_('Delivery'),
                            connection=self.conn)
        service = Service(sellable=sellable, connection=self.conn)
        self._set_schema(key, service.id)


def sysparam(conn):
    return ParameterAccess(conn)


# FIXME: Move to a classmethod on ParameterData
def get_parameter_by_field(field_name, conn):
    data = ParameterData.selectOneBy(field_name=field_name,
                                     connection=conn)
    if data is None:
        raise DatabaseInconsistency(
            "Can't find a ParameterData object for the key %s" %
            field_name)
    return data


def get_foreign_key_parameter(field_name, conn):
    parameter = get_parameter_by_field(field_name, conn)
    if not (parameter and parameter.foreign_key):
        msg = _('There is no defined %s parameter data'
                'in the database.') % field_name
        raise DatabaseInconsistency(msg)
    return parameter


def get_all_details():
    return _details


def get_parameter_details(field_name):
    """ Returns a ParameterDetails class for the given parameter name
    """

    for detail in _details:
        if detail.key == field_name:
            return detail
    else:
        raise NameError("Unknown parameter: %r" % (field_name, ))


#
# Ensuring everything
#

def check_parameter_presence(conn):
    """Check so the number of installed parameters are equal to
    the number of available ones
    @returns: True if they're up to date, False otherwise
    """

    results = ParameterData.select(connection=conn)

    return results.count() == len(_details)


def ensure_system_parameters(update=False):
    # This is called when creating a new database or
    # updating an existing one
    log.info("Creating default system parameters")
    trans = new_transaction()
    param = sysparam(trans)
    if update:
        param.update()
    else:
        param.set_defaults()
    trans.commit(close=True)


def is_developer_mode():
    if os.environ.get('STOQ_DEVELOPER_MODE') == '0':
        return
    return stoqlib.library.uninstalled
