# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source
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
import sys

from kiwi.argcheck import argcheck
from kiwi.datatypes import ValidationError
from kiwi.log import Logger
from kiwi.python import namedAny, ClassInittableObject
from stoqdrivers.enum import TaxType

from stoqlib.database.runtime import get_default_store, new_store
from stoqlib.domain.parameter import ParameterData
from stoqlib.enums import LatePaymentPolicy
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.l10n.l10n import get_l10n_field
from stoqlib.lib.barcode import BarcodeInfo
from stoqlib.lib.countries import get_countries
from stoqlib.lib.kiwilibrary import library
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import (validate_int,
                                    validate_decimal,
                                    validate_directory,
                                    validate_area_code,
                                    validate_percentage)

_ = stoqlib_gettext
log = Logger('stoqlib.parameters')


def _credit_limit_salary_changed(new_value, store):
    from stoqlib.domain.person import Client

    old_value = sysparam(store).CREDIT_LIMIT_SALARY_PERCENT
    if new_value == old_value:
        return

    new_value = Decimal(new_value)
    Client.update_credit_limit(new_value, store)


class PathParameter(object):
    def __init__(self, path):
        self.path = path


class FileParameter(PathParameter):
    pass


class DirectoryParameter(PathParameter):
    pass


class ParameterDetails(object):
    def __init__(self, key, group, short_desc, long_desc, type,
                 initial=None, options=None, combo_data=None, range=None,
                 multiline=False, validator=None, onupgrade=None,
                 change_callback=None):
        self.key = key
        self.group = group
        self.short_desc = short_desc
        self.long_desc = long_desc
        self.type = type
        self.initial = initial
        self.options = options
        self.combo_data = combo_data
        self.range = range
        self.multiline = multiline
        self.validator = validator
        if onupgrade is None:
            onupgrade = initial
        self.onupgrade = onupgrade
        self.change_callback = change_callback

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

    def get_change_callback(self):
        return self.change_callback

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
    def validate_state(value):
        state_l10n = get_l10n_field(get_default_store(), 'state')
        if not state_l10n.validate(value):
            return ValidationError(
                _("'%s' is not a valid %s.")
                % (value, state_l10n.label.lower(), ))

    @staticmethod
    def validate_city(value):
        default_store = get_default_store()
        city_l10n = get_l10n_field(default_store, 'city')
        state = sysparam(default_store).STATE_SUGGESTED
        country = sysparam(default_store).COUNTRY_SUGGESTED
        if not city_l10n.validate(value, state=state, country=country):
            return ValidationError(_("'%s' is not a valid %s.") %
                                   (value, city_l10n.label.lower()))

    #
    #  Private API
    #

    def _get_generic_parameter_validator(self):
        p_type = self.get_parameter_type()

        if issubclass(p_type, int):
            return ParameterDetails.validate_int
        elif issubclass(p_type, Decimal):
            return ParameterDetails.validate_decimal
        elif issubclass(p_type, PathParameter):
            return ParameterDetails.validate_directory

_details = [
    ParameterDetails(
        u'EDIT_CODE_PRODUCT',
        _(u'Products'),
        _(u'Disable edit code products'),
        _(u'Disable edit code products on purchase application'),
        bool, initial=False),

    ParameterDetails(
        u'MAIN_COMPANY',
        _(u'General'),
        _(u'Primary company'),
        _(u'The primary company which is the owner of all other '
          u'branch companies'),
        u'person.Branch'),

    ParameterDetails(
        u'CUSTOM_LOGO_FOR_REPORTS',
        _(u'General'),
        _(u'Custom logotype for reports'),
        _(u'Defines a custom logo for all the reports generated by Stoq. '
          u'The recommended image dimension is 170x65 (pixels), if needed, '
          u'the image will be resized. In order to use the default logotype '
          u'leave this field blank'),
        u'image.Image'),

    ParameterDetails(
        u'DISABLE_COOKIES',
        _(u'General'),
        _(u'Disable cookies'),
        _(u'Disable the ability to use cookies in order to automatic log in '
          u'the system. If so, all the users will have to provide the password '
          u'everytime they log in. Requires restart to take effect.'),
        bool, initial=False),

    ParameterDetails(
        u'DEFAULT_SALESPERSON_ROLE',
        _(u'Sales'),
        _(u'Default salesperson role'),
        _(u'Defines which of the employee roles existent in the system is the '
          u'salesperson role'),
        u'person.EmployeeRole'),

    # FIXME: s/SUGGESTED/DEFAULT/
    ParameterDetails(
        u'SUGGESTED_SUPPLIER',
        _(u'Purchase'),
        _(u'Suggested supplier'),
        _(u'The supplier suggested when we are adding a new product in the '
          u'system'),
        u'person.Supplier'),

    ParameterDetails(
        u'SUGGESTED_UNIT',
        _(u'Purchase'),
        _(u'Suggested unit'),
        _(u'The unit suggested when we are adding a new product in the '
          u'system'),
        u'sellable.SellableUnit'),

    ParameterDetails(
        u'ALLOW_OUTDATED_OPERATIONS',
        _(u'General'),
        _(u'Allow outdated operations'),
        _(u'Allows the inclusion of purchases and payments done previously than the '
          u'current date.'),
        bool, initial=False),

    ParameterDetails(
        u'DELIVERY_SERVICE',
        _(u'Sales'),
        _(u'Delivery service'),
        _(u'The default delivery service in the system.'),
        u'service.Service'),

    # XXX This parameter is POS-specific. How to deal with that
    # in a better way?
    ParameterDetails(
        u'POS_FULL_SCREEN',
        _(u'Sales'),
        _(u'Show POS application in Fullscreen'),
        _(u'Once this parameter is set the Point of Sale application '
          u'will be showed as full screen'),
        bool, initial=False),

    ParameterDetails(
        u'POS_SEPARATE_CASHIER',
        _(u'Sales'),
        _(u'Exclude cashier operations in Point of Sale'),
        _(u'If you have a computer that will be a Point of Sales and have a '
          u'fiscal printer connected, set this False, so the Till menu will '
          u'appear on POS. If you prefer to separate the Till menu from POS '
          u'set this True.'),
        bool, initial=False),

    ParameterDetails(
        u'ENABLE_PAULISTA_INVOICE',
        _(u'Sales'),
        _(u'Enable paulista invoice'),
        _(u'Once this parameter is set, we will be able to join to the '
          u'Sao Paulo state program of fiscal commitment.'),
        bool, initial=False),

    ParameterDetails(
        u'CITY_SUGGESTED',
        _(u'General'),
        _(u'Default city'),
        _(u'When adding a new address for a certain person we will always '
          u'suggest this city.'),
        unicode, initial=u'São Carlos',
        validator=ParameterDetails.validate_city),

    ParameterDetails(
        u'STATE_SUGGESTED',
        _(u'General'),
        _(u'Default state'),
        _(u'When adding a new address for a certain person we will always '
          u'suggest this state.'),
        unicode, initial=u'SP', validator=ParameterDetails.validate_state),

    ParameterDetails(
        u'COUNTRY_SUGGESTED',
        _(u'General'),
        _(u'Default country'),
        _(u'When adding a new address for a certain person we will always '
          u'suggest this country.'),
        # FIXME: When fixing bug 5100, change this to BR
        unicode, initial=u'Brazil', combo_data=get_countries),

    ParameterDetails(
        u'ALLOW_REGISTER_NEW_LOCATIONS',
        _(u'General'),
        _(u'Allow registration of new city locations'),
        # Change the note here when we have more locations to reflect it
        _(u'Allow to register new city locations. A city location is a '
          u'single set of a country + state + city.\n'
          u'NOTE: Right now this will only work for brazilian locations.'),
        bool, initial=False),

    ParameterDetails(
        u'HAS_DELIVERY_MODE',
        _(u'Sales'),
        _(u'Has delivery mode'),
        _(u'Does this branch work with delivery service? If not, the '
          u'delivery option will be disable on Point of Sales Application.'),
        bool, initial=True),

    ParameterDetails(
        u'SHOW_COST_COLUMN_IN_SALES',
        _(u'Sales'),
        _(u'Show cost column in sales'),
        _(u'should the cost column be displayed when creating a new sale quote.'),
        bool, initial=False),

    ParameterDetails(
        u'MAX_SEARCH_RESULTS',
        _(u'General'),
        _(u'Max search results'),
        _(u'The maximum number of results we must show after searching '
          u'in any dialog.'),
        int, initial=600, range=(1, sys.maxint)),

    ParameterDetails(
        u'CONFIRM_SALES_ON_TILL',
        _(u'Sales'),
        _(u'Confirm sales in Till'),
        _(u'Once this parameter is set, the sales confirmation are only made '
          u'on till application and the fiscal coupon will be printed on '
          u'that application instead of Point of Sales'),
        bool, initial=False),

    ParameterDetails(
        u'ACCEPT_CHANGE_SALESPERSON',
        _(u'Sales'),
        _(u'Change salesperson'),
        _(u'Once this parameter is set to true, the user will be '
          u'able to change the salesperson of an opened '
          u'order on sale checkout dialog'),
        bool, initial=False),

    ParameterDetails(
        u'RETURN_MONEY_ON_SALES',
        _(u'Sales'),
        _(u'Return money on sales'),
        _(u'Once this parameter is set the salesperson can return '
          u'money to clients when there is overpaid values in sales '
          u'with gift certificates as payment method.'),
        bool, initial=True),

    ParameterDetails(
        u'MAX_SALE_DISCOUNT',
        _(u'Sales'),
        _(u'Max discount for sales'),
        _(u'The max discount for salesperson in a sale'),
        Decimal, initial=5, range=(0, 100),
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        u'SALE_PAY_COMMISSION_WHEN_CONFIRMED',
        _(u'Sales'),
        _(u'Commission Payment At Sale Confirmation'),
        _(u'Define whether the commission is paid when a sale is confirmed. '
          u'If True pay the commission when a sale is confirmed, '
          u'if False, pay a relative commission for each commission when '
          u'the sales payment is paid.'),
        bool, initial=False),

    ParameterDetails(
        u'ALLOW_TRADE_NOT_REGISTERED_SALES',
        _(u"Sales"),
        _(u"Allow trade not registered sales"),
        _(u"If this is set to True, you will be able to trade products "
          u"from sales not registered on Stoq. Use this option only if "
          u"you need to trade itens sold on other stores."),
        bool, initial=False),

    ParameterDetails(
        u'DEFAULT_OPERATION_NATURE',
        _(u'Sales'),
        _(u'Default operation nature'),
        _(u'When adding a new sale quote, we will always suggest '
          u'this operation nature'),
        unicode, initial=_(u'Sale')),

    ParameterDetails(
        u'ASK_SALES_CFOP',
        _(u'Sales'),
        _(u'Ask for Sale Order C.F.O.P.'),
        _(u'Once this parameter is set to True we will ask for the C.F.O.P. '
          u'when creating new sale orders'),
        bool, initial=False),

    ParameterDetails(
        u'DEFAULT_SALES_CFOP',
        _(u'Sales'),
        _(u'Default Sales C.F.O.P.'),
        _(u'Default C.F.O.P. (Fiscal Code of Operations) used when generating '
          u'fiscal book entries.'),
        u'fiscal.CfopData'),

    ParameterDetails(
        u'DEFAULT_RETURN_SALES_CFOP',
        _(u'Sales'),
        _(u'Default Return Sales C.F.O.P.'),
        _(u'Default C.F.O.P. (Fiscal Code of Operations) used when returning '
          u'sale orders '),
        u'fiscal.CfopData'),

    ParameterDetails(
        u'TOLERANCE_FOR_LATE_PAYMENTS',
        _(u'Sales'),
        _(u'Tolerance for a payment to be considered as a late payment.'),
        _(u'How many days Stoq should allow a client to not pay a late '
          u'payment without considering it late.'),
        int, initial=0, range=(0, 365)),

    ParameterDetails(
        u'LATE_PAYMENTS_POLICY',
        _(u'Sales'),
        _(u'Policy for customers with late payments.'),
        _(u'How should Stoq behave when creating a new sale for a client with '
          u'late payments'),
        int, initial=int(LatePaymentPolicy.ALLOW_SALES),
        options={int(LatePaymentPolicy.ALLOW_SALES): _(u'Allow sales'),
                 int(LatePaymentPolicy.DISALLOW_STORE_CREDIT):
                    _(u'Allow sales except with store credit'),
                 int(LatePaymentPolicy.DISALLOW_SALES): _(u'Disallow sales')}),

    ParameterDetails(
        u'DEFAULT_RECEIVING_CFOP',
        _(u'Purchase'),
        _(u'Default Receiving C.F.O.P.'),
        _(u'Default C.F.O.P. (Fiscal Code of Operations) used when receiving '
          u'products in the stock application.'),
        u'fiscal.CfopData'),

    ParameterDetails(
        u'DEFAULT_STOCK_DECREASE_CFOP',
        _(u'Stock'),
        _(u'Default C.F.O.P. for Stock Decreases'),
        _(u'Default C.F.O.P. (Fiscal Code of Operations) used when performing a '
          u'manual stock decrease.'),
        u'fiscal.CfopData'),

    ParameterDetails(
        u'ICMS_TAX',
        _(u'Sales'),
        _(u'Default ICMS tax'),
        _(u'Default ICMS to be applied on all the products of a sale. ') + u' ' +
        _(u'This is a percentage value and must be between 0 and 100.') + u' ' +
        _(u'E.g: 18, which means 18% of tax.'),
        Decimal, initial=18, range=(0, 100),
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        u'ISS_TAX',
        _(u'Sales'),
        _(u'Default ISS tax'),
        _(u'Default ISS to be applied on all the services of a sale. ') + u' ' +
        _(u'This is a percentage value and must be between 0 and 100.') + u' ' +
        _(u'E.g: 12, which means 12% of tax.'),
        Decimal, initial=18, range=(0, 100),
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        u'SUBSTITUTION_TAX',
        _(u'Sales'),
        _(u'Default Substitution tax'),
        _(u'The tax applied on all sale products with substitution tax type.') +
        u' ' +
        _(u'This is a percentage value and must be between 0 and 100.') + u' ' +
        _(u'E.g: 16, which means 16% of tax.'),
        Decimal, initial=18, range=(0, 100),
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        u'DEFAULT_AREA_CODE',
        _(u'General'),
        _(u'Default area code'),
        _(u'This is the default area code which will be used when '
          u'registering new clients, users and more to the system'),
        int, initial=16,
        validator=ParameterDetails.validate_area_code),

    ParameterDetails(
        u'CREDIT_LIMIT_SALARY_PERCENT',
        _(u'General'),
        _(u"Client's credit limit automatic calculation"),
        _(u"This is used to calculate the client's credit limit according"
          u"to the client's salary. If this percent is changed it will "
          u"automatically recalculate the credit limit for all clients."),
        Decimal, initial=0, range=(0, 100),
        validator=ParameterDetails.validate_percentage,
        change_callback=_credit_limit_salary_changed),

    ParameterDetails(
        u'DEFAULT_PRODUCT_TAX_CONSTANT',
        _(u'Sales'),
        _(u'Default tax constant for products'),
        _(u'This is the default tax constant which will be used '
          u'when adding new products to the system'),
        u'sellable.SellableTaxConstant'),

    ParameterDetails(
        u'LABEL_TEMPLATE_PATH',
        _(u'General'),
        _(u'Glabels template file'),
        _(u'The glabels file that will be used to print the labels. Check'
          u'documentation to see how to setup this file.'),
        FileParameter, initial=u""),

    ParameterDetails(
        u'CAT52_DEST_DIR',
        _(u'General'),
        _(u'Cat 52 destination directory'),
        _(u'Where the file generated after a Z-reduction should be saved.'),
        DirectoryParameter, initial=u'~/.stoq/cat52'),

    ParameterDetails(
        u'COST_PRECISION_DIGITS',
        _(u'General'),
        _(u'Number of digits to use for product cost'),
        _(u'Set this parameter accordingly to the number of digits of the '
          u'products you purchase'),
        int, initial=2, range=(2, 8)),

    ParameterDetails(
        u'SCALE_BARCODE_FORMAT',
        _(u'Sales'),
        _(u'Scale barcode format'),
        _(u'Format used by the barcode printed by the scale. This format always'
          u' starts with 2 followed by 4,5 or 6 digits product code and by a 5'
          u' digit weight or a 6 digit price. Check or scale documentation and'
          u' configuration to see the best option.'),
        int, initial=0,
        options=BarcodeInfo.options),

    ParameterDetails(
        u'NFE_SERIAL_NUMBER',
        _(u'NF-e'),
        _(u'Fiscal document serial number'),
        _(u'Fiscal document serial number. Fill with 0 if the NF-e have no '
          u'series. This parameter only has effect if the nfe plugin is enabled.'),
        int, initial=1),

    ParameterDetails(
        u'NFE_DANFE_ORIENTATION',
        _(u'NF-e'),
        _(u'Danfe printing orientation'),
        _(u'Orientation to use for printing danfe. Portrait or Landscape'),
        int, initial=0,
        options={0: _(u'Portrait'),
                 1: _(u'Landscape')}),

    ParameterDetails(
        u'NFE_FISCO_INFORMATION',
        _(u'NF-e'),
        _(u'Additional Information for the Fisco'),
        _(u'Additional information to add to the NF-e for the Fisco'), unicode,
        initial=(u'Documento emitido por ME ou EPP optante pelo SIMPLES '
                 u'NACIONAL. Não gera Direito a Crédito Fiscal de ICMS e de '
                 u'ISS. Conforme Lei Complementar 123 de 14/12/2006.'),
        multiline=True),

    ParameterDetails(
        u'BANKS_ACCOUNT',
        _(u'Accounts'),
        _(u'Parent bank account'),
        _(u'Newly created bank accounts will be placed under this account.'),
        u'account.Account'),

    ParameterDetails(
        u'TILLS_ACCOUNT',
        _(u'Accounts'),
        _(u'Parent till account'),
        _(u'Till account transfers will be placed under this account'),
        u'account.Account'),

    ParameterDetails(
        u'IMBALANCE_ACCOUNT',
        _(u'Accounts'),
        _(u'Imbalance account'),
        _(u'Account used for unbalanced transactions'),
        u'account.Account'),

    ParameterDetails(
        u'DEMO_MODE',
        _(u'General'),
        _(u'Demonstration mode'),
        _(u'If Stoq is used in a demonstration mode'),
        bool, initial=False),

    ParameterDetails(
        u'BLOCK_INCOMPLETE_PURCHASE_PAYMENTS',
        _(u'Payments'),
        _(u'Block incomplete purchase payments'),
        _(u'Do not allow confirming a account payable if the purchase is not '
          u'completely received.'),
        bool, initial=False),

    ParameterDetails(
        u'CREATE_PAYMENTS_ON_STOCK_DECREASE',
        _(u'Payments'),
        _(u'Create payments for a stock decrease'),
        _(u'When this paramater is True, Stoq will allow to create payments for'
          u'stock decreases.'),
        bool, initial=False),

    # This parameter is tricky, we want to ask the user to fill it in when
    # upgrading from a previous version, but not if the user installed Stoq
    # from scratch. Some of the hacks involved with having 3 boolean values
    # ("", True, False) can be removed if we always allow None and treat it like
    # and unset value in the database.
    ParameterDetails(
        u'ONLINE_SERVICES',
        _(u'General'),
        _(u'Online services'),
        _(u'If online services such as upgrade notifications, automatic crash reports '
          u'should be enabled.'),
        bool, initial=True, onupgrade=u''),

    ParameterDetails(
        u'BILL_INSTRUCTIONS',
        _(u'Sales'),
        _(u'Bill instructions '),
        # Translators: do not translate $DATE
        _(u'When printing bills, include the first 3 lines of these on '
          u'the bill itself. This usually includes instructions on how '
          u'to pay the bill and the validity and the terms. $DATE will be'
          u'replaced with the due date of the bill'),
        unicode, multiline=True, initial=u""),

    ParameterDetails(
        u'BOOKLET_INSTRUCTIONS',
        _(u'Sales'),
        _(u'Booklet instructions '),
        _(u'When printing booklets, include the first 4 lines of these on it. '
          u'This usually includes instructions on how to pay the booklet and '
          u'the validity and the terms.'),
        unicode, multiline=True,
        initial=_(u"Payable at any branch on presentation of this booklet")),

    ParameterDetails(
        u'SMART_LIST_LOADING',
        _(u'Smart lists'),
        _(u'Load items intelligently from the database'),
        _(u'This is useful when you have several thousand items, but it may cause '
          u'some problems as it\'s new and untested. If you want to preserve the old '
          u'list behavior in the payable and receivable applications, '
          u'disable this parameter.'),
        bool,
        initial=True),

    ParameterDetails(
        u'LOCAL_BRANCH',
        _(u'General'),
        _(u'Current branch for this database'),
        _(u'When operating with synchronized databases, this parameter will be '
          u'used to restrict the data that will be sent to this database.'),
        u'person.Branch'),

    ParameterDetails(
        u'SYNCHRONIZED_MODE',
        _(u'General'),
        _(u'Synchronized mode operation'),
        _(u'This parameter indicates if Stoq is operating with synchronized '
          u'databases. When using synchronized databases, some operations with '
          u'branches different than the current one will be restriced.'),
        bool,
        initial=False),

    ParameterDetails(
        u'PRINT_PROMISSORY_NOTES_ON_BOOKLETS',
        _(u'Payments'),
        _(u'Printing of promissory notes on booklets'),
        _(u'This parameter indicates if Stoq should print promissory notes when'
          u' printing booklets for payments.'),
        bool,
        initial=True),

    ParameterDetails(
        u'PRINT_PROMISSORY_NOTE_ON_LOAN',
        _(u'Sales'),
        _(u'Printing of promissory notes on loans'),
        _(u'This parameter indicates if Stoq should print a promissory note '
          u'when printing a loan receipt.'),
        bool, initial=False),
    ]


class ParameterAccess(ClassInittableObject):
    """A mechanism to tie specific instances to constants that can be
    made available cross-application. This class has a special hook that
    allows the values to be looked up on-the-fly and cached.

    Usage:

    >>> from stoqlib.lib.parameters import sysparam
    >>> from stoqlib.database.runtime import get_default_store
    >>> default_store = get_default_store()
    >>> parameter = sysparam(default_store).EDIT_CODE_PRODUCT

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

    def __init__(self, store):
        ClassInittableObject.__init__(self)
        self.store = store

    def _remove_unused_parameters(self):
        """Remove any  parameter found in ParameterData table which is not
        used any longer.
        """
        detail_keys = [detail.key for detail in _details]
        for param in self.store.find(ParameterData):
            if param.field_name not in detail_keys:
                self.store.remove(param)

    def _set_schema(self, field_name, field_value, is_editable=True):
        if field_value is not None:
            field_value = unicode(field_value)

        data = self.store.find(ParameterData,
                               field_name=field_name).one()
        if data is None:
            store = new_store()
            ParameterData(store=store,
                          field_name=field_name,
                          field_value=field_value,
                          is_editable=is_editable)
            store.commit(close=True)
        else:
            data.field_value = field_value

    def _set_default_value(self, detail, initial):
        if initial is None:
            return

        value = initial
        if detail.type is bool:
            if value != u"":
                value = int(initial)
        self._set_schema(detail.key, value)

    def _create_default_values(self):
        # Create default values for parameters that take objects
        self._create_default_image()
        self._create_default_sales_cfop()
        self._create_default_return_sales_cfop()
        self._create_default_receiving_cfop()
        self._create_default_stock_decrease_cfop()
        self._create_suggested_supplier()
        self._create_suggested_unit()
        self._create_default_salesperson_role()
        self._create_main_company()
        self._create_delivery_service()
        self._create_product_tax_constant()
        self._create_current_branch()

    def _create_default_image(self):
        from stoqlib.domain.image import Image
        key = u"CUSTOM_LOGO_FOR_REPORTS"
        if self.get_parameter_by_field(key, Image):
            return
        self._set_schema(key, None)

    def _create_suggested_supplier(self):
        from stoqlib.domain.person import Supplier
        key = u"SUGGESTED_SUPPLIER"
        if self.get_parameter_by_field(key, Supplier):
            return
        self._set_schema(key, None)

    def _create_suggested_unit(self):
        from stoqlib.domain.sellable import SellableUnit
        key = u"SUGGESTED_UNIT"
        if self.get_parameter_by_field(key, SellableUnit):
            return
        self._set_schema(key, None)

    def _create_default_salesperson_role(self):
        from stoqlib.domain.person import EmployeeRole
        key = u"DEFAULT_SALESPERSON_ROLE"
        if self.get_parameter_by_field(key, EmployeeRole):
            return
        store = new_store()
        role = EmployeeRole(name=_(u'Salesperson'),
                            store=store)
        store.commit(close=True)
        self._set_schema(key, role.id, is_editable=False)

    def _create_main_company(self):
        from stoqlib.domain.person import Branch
        key = u"MAIN_COMPANY"
        if self.get_parameter_by_field(key, Branch):
            return
        self._set_schema(key, None)

    def _create_delivery_service(self):
        from stoqlib.domain.service import Service
        key = u"DELIVERY_SERVICE"
        if self.get_parameter_by_field(key, Service):
            return

        self.create_delivery_service()

    def _create_cfop(self, key, description, code):
        from stoqlib.domain.fiscal import CfopData
        if self.get_parameter_by_field(key, CfopData):
            return
        data = self.store.find(CfopData, code=code).one()
        if not data:
            store = new_store()
            data = CfopData(code=code, description=description,
                            store=store)
        store.commit(close=True)
        self._set_schema(key, data.id)

    def _create_default_return_sales_cfop(self):
        self._create_cfop(u"DEFAULT_RETURN_SALES_CFOP",
                          u"Devolucao",
                          u"5.202")

    def _create_default_sales_cfop(self):
        self._create_cfop(u"DEFAULT_SALES_CFOP",
                          u"Venda de Mercadoria Adquirida",
                          u"5.102")

    def _create_default_receiving_cfop(self):
        self._create_cfop(u"DEFAULT_RECEIVING_CFOP",
                          u"Compra para Comercializacao",
                          u"1.102")

    def _create_default_stock_decrease_cfop(self):
        self._create_cfop(u"DEFAULT_STOCK_DECREASE_CFOP",
                          u"Outra saída de mercadoria ou "
                          u"prestação de serviço não especificado",
                          u"5.949")

    def _create_product_tax_constant(self):
        from stoqlib.domain.sellable import SellableTaxConstant
        key = u"DEFAULT_PRODUCT_TAX_CONSTANT"
        if self.get_parameter_by_field(key, SellableTaxConstant):
            return

        tax_constant = SellableTaxConstant.get_by_type(
            TaxType.NONE, self.store)
        self._set_schema(key, tax_constant.id)

    def _create_current_branch(self):
        from stoqlib.domain.person import Branch
        key = u"LOCAL_BRANCH"
        if self.get_parameter_by_field(key, Branch):
            return

        self._set_schema(key, None, is_editable=False)

    #
    # Public API
    #

    @argcheck(unicode, object)
    def update_parameter(self, parameter_name, value):
        if parameter_name in [u'DEMO_MODE', u'LOCAL_BRANCH', u'SYNCHRONIZED_MODE']:
            raise AssertionError
        param = get_parameter_by_field(parameter_name, self.store)
        param.field_value = unicode(value)
        self.rebuild_cache_for(parameter_name)

    def rebuild_cache_for(self, param_name):
        from stoqlib.domain.base import Domain
        try:
            value = self._cache[param_name]
        except KeyError:
            return

        param = get_parameter_by_field(param_name, self.store)
        value_type = type(value)
        if not issubclass(value_type, Domain):
            # XXX: workaround to works with boolean types:
            data = param.field_value
            if value_type is bool:
                if data == u'True':
                    data = True
                elif data == u'False':
                    data = False
                else:
                    data = bool(int(data))
            # this is necessary to avoid errors when the user writes an
            # invalid input value for int fields
            if value_type is int and not data:
                initial = get_parameter_details(param.field_name).initial
                if initial is not None:
                    data = initial
                else:
                    data = 0
            self._cache[param_name] = value_type(data)
            return
        table = value_type
        obj_id = param.field_value
        if not obj_id:
            del self._cache[param_name]
            return

        self._cache[param_name] = self.store.get(table, int(obj_id))

    @classmethod
    def clear_cache(cls):
        log.info("Clearing cache")
        cls._cache = {}

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
        from stoqlib.domain.base import Domain
        if isinstance(field_type, basestring):
            field_type = namedAny('stoqlib.domain.' + field_type)
        if field_name in self._cache:
            param = self._cache[field_name]
            if issubclass(field_type, Domain):
                return field_type.get(param.id, store=self.store)
            elif issubclass(field_type, PathParameter):
                return param
            else:
                return field_type(param)
        value = self.store.find(ParameterData, field_name=field_name).one()
        if value is None:
            return
        if issubclass(field_type, Domain):
            if value.field_value == u'' or value.field_value is None:
                return
            param = self.store.get(field_type, int(value.field_value))
            if param is None:
                return None
        else:
            # XXX: workaround to works with boolean types:
            value = value.field_value
            if field_type is bool:
                if value == u'True':
                    param = True
                elif value == u'False':
                    param = False
                # This is a pre-1.0 migration specific hack
                elif value == u"":
                    return None
                else:
                    param = bool(int(value))
            elif field_type is unicode:
                param = value
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
        key = u"DELIVERY_SERVICE"
        store = new_store()
        tax_constant = SellableTaxConstant.get_by_type(TaxType.SERVICE, store)
        sellable = Sellable(description=_(u'Delivery'),
                            store=store)
        sellable.tax_constant = tax_constant
        service = Service(sellable=sellable, store=store)
        self._set_schema(key, service.id)
        store.commit(close=True)


def sysparam(store):
    return ParameterAccess(store)


# FIXME: Move to a classmethod on ParameterData
def get_parameter_by_field(field_name, store):
    data = store.find(ParameterData, field_name=field_name).one()
    if data is None:
        raise DatabaseInconsistency(
            "Can't find a ParameterData object for the key %s" %
            field_name)
    return data


def get_foreign_key_parameter(field_name, store):
    parameter = get_parameter_by_field(field_name, store)
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

def check_parameter_presence(store):
    """Check so the number of installed parameters are equal to
    the number of available ones
    :returns: True if they're up to date, False otherwise
    """

    results = store.find(ParameterData)

    return results.count() == len(_details)


def ensure_system_parameters(update=False):
    # This is called when creating a new database or
    # updating an existing one
    log.info("Creating default system parameters")
    store = new_store()
    param = sysparam(store)
    if update:
        param.update()
    else:
        param.set_defaults()
    store.commit(close=True)


def is_developer_mode():
    if os.environ.get('STOQ_DEVELOPER_MODE') == '0':
        return
    return library.uninstalled
