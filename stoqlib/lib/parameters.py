# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2005-2013 Async Open Source
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#
""" Parameters and system data for applications"""

import collections
from decimal import Decimal
from uuid import uuid4
import logging

from kiwi.datatypes import ValidationError
from stoqdrivers.enum import TaxType

from stoqlib.database.runtime import get_default_store
from stoqlib.domain.parameter import ParameterData
from stoqlib.enums import (LatePaymentPolicy, ReturnPolicy,
                           ChangeSalespersonPolicy)
from stoqlib.l10n.l10n import get_l10n_field
from stoqlib.lib.barcode import BarcodeInfo
from stoqlib.lib.countries import get_countries
from stoqlib.lib.defaults import MAX_INT
from stoqlib.lib.importutils import import_from_string
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import (validate_int,
                                    validate_decimal,
                                    validate_area_code,
                                    validate_percentage,
                                    validate_cnpj)

_ = stoqlib_gettext
log = logging.getLogger(__name__)


def _credit_limit_salary_changed(new_value, store):
    from stoqlib.domain.person import Client

    old_value = sysparam.get_decimal('CREDIT_LIMIT_SALARY_PERCENT')
    if new_value == old_value:
        return

    new_value = Decimal(new_value)
    Client.update_credit_limit(new_value, store)


class ParameterDetails(object):

    def __init__(self, key, group, short_desc, long_desc, type,
                 initial=None, options=None, combo_data=None, range=None,
                 multiline=False, validator=None,
                 change_callback=None, editor=None, wrap=True,
                 allow_none=False, is_editable=True, check_missing=None):
        """
        :param check_missing: A callable that should return True or False
          indicating if the parameter is missing configuration. If missing, it
          will be highlighted in the parameters search
        """
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
        self.change_callback = change_callback
        self.editor = editor
        self.wrap = wrap
        self.allow_none = allow_none
        self.is_editable = is_editable
        self.check_missing = check_missing

    #
    #  Public API
    #

    def get_parameter_type(self):
        if isinstance(self.type, str):
            return import_from_string('stoqlib.domain.' + self.type)
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
    def validate_cnpj(value):
        if not validate_cnpj(value):
            return ValidationError(_("'%s' is not a valid CNPJ"))

    @staticmethod
    def validate_state(value):
        state_l10n = get_l10n_field('state')
        if not state_l10n.validate(value):
            return ValidationError(
                _("'%s' is not a valid %s.")
                % (value, state_l10n.label.lower(), ))

    @staticmethod
    def validate_city(value):
        city_l10n = get_l10n_field('city')
        state = sysparam.get_string('STATE_SUGGESTED')
        country = sysparam.get_string('COUNTRY_SUGGESTED')
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


DEFAULT_LOAN_NOTICE = _(
    'I inform and sign up to receive the items in full '
    'working order and I am aware of the responsability '
    'that I have for returning them, as well as the '
    'return of the amounts involved, in case of loss, '
    'damage or any event that make the product unusable.')


_details = [
    ParameterDetails(
        'EDIT_CODE_PRODUCT',
        _('Products'),
        _('Disable edit code products'),
        _('Disable edit code products on purchase application'),
        bool, initial=False),

    ParameterDetails(
        'SUGGEST_PRODUCT_CODE_BASED_CATEGORY',
        _('Products'),
        _('Suggest product code based on the selected category'),
        _('If the next product code should be based on the category selected or not'),
        bool, initial=False),

    ParameterDetails(
        'BARCODE_MAX_SIZE',
        _('Products'),
        _('Max size for product barcodes'),
        _('Max number of digits for product barcodes'),
        int, initial=14),

    ParameterDetails(
        'DEFAULT_PRODUCT_PIS_TEMPLATE',
        _('Products'),
        _('Default PIS template'),
        _('Use this information when try to emmit a fiscal document and the '
          'product has no configured PIS'),
        'taxes.ProductPisTemplate'),

    ParameterDetails(
        'DEFAULT_PRODUCT_COFINS_TEMPLATE',
        _('Products'),
        _('Default COFINS template'),
        _('Use this information when try to emmit a fiscal document and the '
          'product has no configured COFINS'),
        'taxes.ProductCofinsTemplate'),

    ParameterDetails(
        'LABEL_COLUMNS',
        _('Products'),
        _('Label columns'),
        _('Which columns we should print on label'),
        str, initial='code,barcode,description,price'),

    ParameterDetails(
        'MAIN_COMPANY',
        _('General'),
        _('Primary company'),
        _('The primary company which is the owner of all other '
          'branch companies'),
        'person.Branch'),

    ParameterDetails(
        'CUSTOM_LOGO_FOR_REPORTS',
        _('General'),
        _('Custom logotype for reports'),
        _('Defines a custom logo for all the reports generated by Stoq. '
          'The recommended image dimension is 170x65 (pixels), if needed, '
          'the image will be resized. In order to use the default logotype '
          'leave this field blank'),
        'image.Image'),

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
        'person.Supplier', allow_none=True),

    ParameterDetails(
        'SUGGESTED_UNIT',
        _('Purchase'),
        _('Suggested unit'),
        _('The unit suggested when we are adding a new product in the '
          'system'),
        'sellable.SellableUnit'),

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
        'DEFAULT_SCALE_TOKEN_PRODUCT',
        _('Sales'),
        _('Default Scale Token Product'),
        _('Default product that will be automatically added to a sale token '
          'when the sale token is read'),
        'product.Product', initial=None),

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
        'USE_SALE_TOKEN',
        _('Sales'),
        _('Use tokens to control sales'),
        _('A token is a phisical object that will be attached to a sale '
          'during its lifetime. For example, it can be a bar table, a '
          'hotel room, a real token in a convenience store and so on. '),
        bool, initial=False),

    ParameterDetails(
        'DEFAULT_PAYMENT_METHOD',
        _('Sales'),
        _('Default payment method selected'),
        _('The default method to select when doing a checkout on POS'),
        'payment.method.PaymentMethod'),

    ParameterDetails(
        'ALLOW_CANCEL_CONFIRMED_SALES',
        _('Sales'),
        _('Allow to cancel confirmed sales'),
        _('When this parameter is True, allow the user to cancel confirmed and'
          ' paid sales'),
        bool, initial=False),

    ParameterDetails(
        'ALLOW_CANCEL_ORDERED_SALES',
        _('Sales'),
        _('Allow to cancel ordered sales'),
        _('When this parameter is True, allow the user to cancel ordered and'
          ' paid sales'),
        bool, initial=False),

    ParameterDetails(
        'CITY_SUGGESTED',
        _('General'),
        _('Default city'),
        _('When adding a new address for a certain person we will always '
          'suggest this city.'),
        str, initial='São Carlos',
        validator=ParameterDetails.validate_city),

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
        # FIXME: When fixing bug 5100, change this to BR
        str, initial='Brazil', combo_data=get_countries),

    ParameterDetails(
        'ALLOW_REGISTER_NEW_LOCATIONS',
        _('General'),
        _('Allow registration of new city locations'),
        # Change the note here when we have more locations to reflect it
        _('Allow to register new city locations. A city location is a '
          'single set of a country + state + city.\n'
          'NOTE: Right now this will only work for brazilian locations.'),
        bool, initial=False),

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
        int, initial=600, range=(1, MAX_INT)),

    ParameterDetails(
        'TILL_TOLERANCE_FOR_CLOSING',
        _('Till'),
        _('Till tolerance for closing'),
        _('Tolerance time for closing the till'),
        int, initial=0, range=(0, 22)),

    ParameterDetails(
        'INCLUDE_CASH_FUND_ON_TILL_CLOSING',
        _('Till'),
        _('Include cash fund on till closing'),
        _('Makes stoq expects to include the cash fund on till closing'),
        bool, initial=False),

    ParameterDetails(
        'TILL_BLIND_CLOSING',
        _('Till'),
        _('Use blind closing for till'),
        _('When set, the user will perform a blind till closing, ie, he will not know '
          'the values that are supposed to be in the till and will only inform the '
          'quantity he counted for each payment method'),
        bool, initial=False),

    ParameterDetails(
        'CONFIRM_SALES_ON_TILL',
        _('Sales'),
        _('Confirm sales in Till'),
        _('Once this parameter is set, the sales confirmation are only made '
          'on till application and the fiscal coupon will be printed on '
          'that application instead of Point of Sales'),
        bool, initial=False),

    ParameterDetails(
        'CONFIRM_QTY_ON_BARCODE_ACTIVATE',
        _('Sales'),
        _('Requires quantity confirmation after barcode activation'),
        _('The system will always require the quantity of products '
          'before adding a sale item on Point of Sale'),
        bool, initial=False),

    ParameterDetails(
        'DEFAULT_TABLE_PRICE',
        _('Sales'),
        _('Default table price'),
        _('Default table price that will be used when selling products. This table price will be '
          'used instead of the default price configured in the product/service. Useful when a '
          'branch should have a special price for the products.'),
        'person.ClientCategory', allow_none=True),

    ParameterDetails(
        'POS_ALLOW_CHANGE_PRICE',
        _('POS'),
        _('Allow to change sellable price in POS app'),
        _('When adding a sellable do a sale in the POS app, should the user be '
          'allowed to edit the sale price of the selected sellable. This '
          'depends on the parameter "Require quantity confirmation after '
          'barcode activation"'),
        bool, initial=True),

    ParameterDetails(
        'ACCEPT_CHANGE_SALESPERSON',
        _('Sales'),
        _('Change salesperson'),
        _('Determines weather we are able or not to change the salesperson '
          'on the sale checkout dialog. Both "Allowed" and "Disallowed" will '
          'select the current user by default, but only the former will '
          'allow it to be changed. "Choose" will force the current user to '
          'indicate the correct salesperson.'),
        int, initial=int(ChangeSalespersonPolicy.DISALLOW),
        options={
            int(ChangeSalespersonPolicy.DISALLOW): _('Disallowed'),
            int(ChangeSalespersonPolicy.ALLOW): _(u"Allowed"),
            int(ChangeSalespersonPolicy.FORCE_CHOOSE): _('Choose'),
        }),

    ParameterDetails(
        'RETURN_POLICY_ON_SALES',
        _('Sales'),
        _('Return policy on sales'),
        _('This parameter sets if the salesperson must return money, credit '
          'or if the client can choose when there is overpaid values in '
          'sales.'),
        int, initial=int(ReturnPolicy.CLIENT_CHOICE),
        options={
            int(ReturnPolicy.CLIENT_CHOICE): _(u"Client's choice"),
            int(ReturnPolicy.RETURN_MONEY): _('Always return money'),
            int(ReturnPolicy.RETURN_CREDIT): _('Always create credit for '
                                               'future sales'),
        }),

    ParameterDetails(
        'ACCEPT_SALE_RETURN_WITHOUT_DOCUMENT',
        _('Sales'),
        _('Allow sale return from clients without document'),
        _('If this parameter is set it will not be possible to accept '
          'returned sales from clients without document.'),
        bool, initial=True),

    ParameterDetails(
        'MAX_SALE_DISCOUNT',
        _('Sales'),
        _('Max discount for sales'),
        _('The max discount for salesperson in a sale'),
        Decimal, initial=Decimal(5), range=(0, 100),
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        'REUTILIZE_DISCOUNT',
        _('Sales'),
        _('Reutilize not used discounts on sale quotes'),
        _('Whether we should reutilize the discount not used on some '
          'products to other products. For instance, if two products with '
          'a price of 100,00 are on a sale, and they both have a max '
          'discount of 10%, that means we could sell each one for 90,00. '
          'If this parameter is true, we could still sell one of those '
          'items for 100,00 and reutilize it\'s not used discount on the '
          'other product, selling it for 80,00'),
        bool, initial=False),

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
        'ALLOW_TRADE_NOT_REGISTERED_SALES',
        _(u"Sales"),
        _(u"Allow trade not registered sales"),
        _(u"If this is set to True, you will be able to trade products "
          u"from sales not registered on Stoq. Use this option only if "
          u"you need to trade itens sold on other stores."),
        bool, initial=False),

    ParameterDetails(
        'USE_TRADE_AS_DISCOUNT',
        _('Sales'),
        _('Use trade value as a discount'),
        _('The traded value will be used as discount '
          'when confirm a new sale. Otherwise, the trade '
          'will be registred as a new payment for that new sale.'),
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
        'ALLOW_HIGHER_SALE_PRICE',
        _('Sales'),
        _('Allow product sale with a higher price'),
        _('When this parameter is set, we will allow the sales person to add '
          'items to a quote with a price higher than the default price for '
          'the product.'),
        bool, initial=True),

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
        'TOLERANCE_FOR_LATE_PAYMENTS',
        _('Sales'),
        _('Tolerance for a payment to be considered as a late payment.'),
        _('How many days Stoq should allow a client to not pay a late '
          'payment without considering it late.'),
        int, initial=0, range=(0, 365)),

    ParameterDetails(
        'EXPIRATION_SALE_QUOTE_DATE',
        _('Sales'),
        _('Period of time in days to calculate expiration date of a sale quote'),
        _('How many days Stoq should consider to calculate the default '
          'expiration day of a sale quote'),
        int, initial=0, range=(0, 365)),

    ParameterDetails(
        'LATE_PAYMENTS_POLICY',
        _('Sales'),
        _('Policy for customers with late payments.'),
        _('How should Stoq behave when creating a new sale for a client with '
          'late payments'),
        int, initial=int(LatePaymentPolicy.ALLOW_SALES),
        options={int(LatePaymentPolicy.ALLOW_SALES): _('Allow sales'),
                 int(LatePaymentPolicy.DISALLOW_STORE_CREDIT):
                 _('Allow sales except with store credit'),
                 int(LatePaymentPolicy.DISALLOW_SALES): _('Disallow sales')}),

    ParameterDetails(
        'CHANGE_CLIENT_AFTER_CONFIRMED',
        _('Sales'),
        _('Allow client change after sale\'s confirmation'),
        _('This parameter allows to change the client after a sale\'s confirmation.'),
        bool, initial=False),

    ParameterDetails(
        'CHANGE_SALESPERSON_AFTER_CONFIRMED',
        _('Sales'),
        _('Allow salesperson change after sale\'s confirmation'),
        _('This parameter allows to change the salesperson after a sale\'s confirmation.'),
        bool, initial=False),

    ParameterDetails(
        'DEFAULT_RECEIVING_CFOP',
        _('Purchase'),
        _('Default Receiving C.F.O.P.'),
        _('Default C.F.O.P. (Fiscal Code of Operations) used when receiving '
          'products in the stock application.'),
        'fiscal.CfopData'),

    ParameterDetails(
        'DEFAULT_PURCHASE_RETURN_CFOP',
        _('Purchase'),
        _('Default Purchase Return C.F.O.P.'),
        _('Default C.F.O.P. (Fiscal Code of Operations) used when returning '
          'a purchase in the stock application.'),
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
        Decimal, initial=Decimal(18), range=(0, 100),
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        'ISS_TAX',
        _('Sales'),
        _('Default ISS tax'),
        _('Default ISS to be applied on all the services of a sale. ') + ' ' +
        _('This is a percentage value and must be between 0 and 100.') + ' ' +
        _('E.g: 12, which means 12% of tax.'),
        Decimal, initial=Decimal(18), range=(0, 100),
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        'SUBSTITUTION_TAX',
        _('Sales'),
        _('Default Substitution tax'),
        _('The tax applied on all sale products with substitution tax type.') +
        ' ' +
        _('This is a percentage value and must be between 0 and 100.') + ' ' +
        _('E.g: 16, which means 16% of tax.'),
        Decimal, initial=Decimal(18), range=(0, 100),
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
        'CREDIT_LIMIT_SALARY_PERCENT',
        _('General'),
        _(u"Client's credit limit automatic calculation"),
        _(u"This is used to calculate the client's credit limit according"
          u"to the client's salary. If this percent is changed it will "
          u"automatically recalculate the credit limit for all clients."),
        Decimal, initial=Decimal(0), range=(0, 100),
        validator=ParameterDetails.validate_percentage,
        change_callback=_credit_limit_salary_changed),

    ParameterDetails(
        'DEFAULT_PRODUCT_TAX_CONSTANT',
        _('Sales'),
        _('Default tax constant for products'),
        _('This is the default tax constant which will be used '
          'when adding new products to the system'),
        'sellable.SellableTaxConstant'),

    ParameterDetails(
        'SUGGEST_BATCH_NUMBER',
        _('General'),
        _('Suggest batch number'),
        _(u"If false, you should enter the batch number by hand. That's "
          u"useful if the batch number is already present on the barcode "
          u"of the products for instance. If true a sequencial number will "
          u"be used for suggestion when registering new batches. That's "
          u"useful if you generate your own batches."),
        bool, initial=False),

    ParameterDetails(
        'LABEL_TEMPLATE_PATH',
        _('General'),
        _('Glabels template file'),
        _('The glabels file that will be used to print the labels. Check the '
          'documentation to see how to setup this file.'),
        str, initial=u"", editor='file-chooser'),

    ParameterDetails(
        'COST_PRECISION_DIGITS',
        _('General'),
        _('Number of digits to use for product cost'),
        _('Set this parameter accordingly to the number of digits of the '
          'products you purchase'),
        int, initial=2, range=(2, 8)),

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
        'SALES_ACCOUNT',
        _('Accounts'),
        _(u"Sales' payments account"),
        _('Receivable payments originated from sales will default to this account'),
        'account.Account'),

    ParameterDetails(
        'DEMO_MODE',
        _('General'),
        _('Demonstration mode'),
        _('If Stoq is used in a demonstration mode'),
        bool, initial=False, is_editable=False),

    ParameterDetails(
        'BLOCK_PAYMENT_FOR_IMBALANCE_ACCOUNT',
        _('Payments'),
        _('Block payments from/to the imbalance account'),
        _('When set, the user will be required to inform both source and destination '
          'accounts that are different than the imbalance account'),
        bool, initial=False),

    ParameterDetails(
        'BLOCK_INCOMPLETE_PURCHASE_PAYMENTS',
        _('Payments'),
        _('Block incomplete purchase payments'),
        _('Do not allow confirming a account payable if the purchase is not '
          'completely received.'),
        bool, initial=False),

    ParameterDetails(
        'CREATE_PAYMENTS_ON_STOCK_DECREASE',
        _('Payments'),
        _('Create payments for a stock decrease'),
        _('When this paramater is True, Stoq will allow to create payments for '
          'stock decreases.'),
        bool, initial=False),

    ParameterDetails(
        'SHOW_TOTAL_PAYMENTS_ON_TILL',
        _('Till'),
        _('Show total received payments of the day on till'),
        _('When this paramater is True, show total of received payments.'),
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
        bool, initial=True),

    ParameterDetails(
        'BILL_INSTRUCTIONS',
        _('Sales'),
        _('Bill instructions '),
        # Translators: do not translate $DATE, $INTEREST, $PENALTY
        # and $INVOICE_NUMBER
        _('When printing bills, include the first 3 lines of these on '
          'the bill itself. This usually includes instructions on how '
          'to pay the bill and the validity and the terms. The following '
          'placeholders will be replaced by:\n\n'
          '$DATE: Replaced with the due date of the bill\n'
          '$PENALTY: The calculated penalty based on the parameter aliquot\n'
          '$INTEREST: The calculated interest based on the parameter aliquot\n'
          '$DISCOUNT: The calculated discount based on the parameter aliquot\n'
          '$INVOICE_NUMBER: The sale invoice number\n'),
        str, multiline=True, initial=u""),

    ParameterDetails(
        'BILL_PAYMENT_PLACE',
        _('Sales'),
        _('Bill payment place'),
        _('Payment place instructions to be printed on bill slip'),
        str, multiline=True, initial=_('Payable in any bank until due date')),

    ParameterDetails(
        'BILL_INTEREST',
        _('Sales'),
        _('Bill interest aliquot'),
        _('The aliquot to calculate the daily interest on the bill. '
          'See "Bill instructions" parameter for more information on how '
          'this is used'),
        Decimal, initial=Decimal(0), range=(0, 100),
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        'BILL_PENALTY',
        _('Sales'),
        _('Bill penalty aliquot'),
        _('The aliquot to calculate the penalty on the bill. '
          'See "Bill instructions" parameter for more information on how '
          'this is used'),
        Decimal, initial=Decimal(0), range=(0, 100),
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        'BILL_DISCOUNT',
        _('Sales'),
        _('Bill discount aliquot'),
        _('The aliquot to calculate the discount on the bill. '
          'See "Bill instructions" parameter for more information on how '
          'this is used'),
        Decimal, initial=Decimal(0), range=(0, 100),
        validator=ParameterDetails.validate_percentage),

    ParameterDetails(
        'BOOKLET_INSTRUCTIONS',
        _('Sales'),
        _('Booklet instructions '),
        _('When printing booklets, include the first 4 lines of these on it. '
          'This usually includes instructions on how to pay the booklet and '
          'the validity and the terms.'),
        str, multiline=True,
        initial=_(u"Payable at any branch on presentation of this booklet")),

    ParameterDetails(
        'SMART_LIST_LOADING',
        _('Smart lists'),
        _('Load items intelligently from the database'),
        _('This is useful when you have several thousand items, but it may cause '
          'some problems as it\'s new and untested. If you want to preserve the old '
          'list behavior in the payable and receivable applications, '
          'disable this parameter.'),
        bool,
        initial=True),

    ParameterDetails(
        'LOCAL_BRANCH',
        _('General'),
        _('Current branch for this database'),
        _('When operating with synchronized databases, this parameter will be '
          'used to restrict the data that will be sent to this database.'),
        'person.Branch', is_editable=False),

    ParameterDetails(
        'SYNCHRONIZED_MODE',
        _('General'),
        _('Synchronized mode operation'),
        _('This parameter indicates if Stoq is operating with synchronized '
          'databases. When using synchronized databases, some operations with '
          'branches different than the current one will be restriced.'),
        bool,
        initial=False, is_editable=False),

    ParameterDetails(
        'PRINT_PROMISSORY_NOTES_ON_BOOKLETS',
        _('Payments'),
        _('Printing of promissory notes on booklets'),
        _('This parameter indicates if Stoq should print promissory notes when'
          ' printing booklets for payments.'),
        bool,
        initial=True),

    ParameterDetails(
        'PRINT_PROMISSORY_NOTE_ON_LOAN',
        _('Loan'),
        _('Printing of promissory notes on loans'),
        _('This parameter indicates if Stoq should print a promissory note '
          'when printing a loan receipt.'),
        bool, initial=False),

    ParameterDetails(
        'LOAN_NOTICE',
        _('Loan'),
        _('Notice that will be added to the loan report'),
        _('This notice will be added to the loan receipt and can be used to '
          'warn the client that he is responsible for the items he is loaning'),
        str, multiline=True, initial=DEFAULT_LOAN_NOTICE),

    ParameterDetails(
        'PRINT_SALE_DETAILS_ON_POS',
        _('Sales'),
        _('Printing of sale details on point of sales'),
        _('This parameter indicates if Stoq should print the sale details'
          'when finishing a sale on point of sales.'),
        bool, initial=False),

    ParameterDetails(
        'MANDATORY_CHECK_NUMBER',
        _('Payments'),
        _('Mandatory check number'),
        _('This parameter indicates if the check number on check payments is '
          'mandatory.'),
        bool, initial=False),

    ParameterDetails(
        'ALLOW_CREATE_PAYMENT_ON_SALE_QUOTE',
        _('Sales'),
        _('Allow to add payment on sale quote'),
        _('When enabled, the sale quote wizard will have an extra step to '
          'configure the payments for the sale.'),
        bool, initial=False),

    ParameterDetails(
        'MANDATORY_CARD_AUTH_NUMBER',
        _('Sales'),
        _('Set authorization number mandatory'),
        _('Set the authorization number on card payments as mandatory or not.'),
        bool, initial=False),

    ParameterDetails(
        'DEFECT_DETECTED_TEMPLATE',
        _('Work order'),
        _('Defect detected template for work orders'),
        _('A template to be used to fill the "Defect detected" field when '
          'creating a new work order.'),
        str, multiline=True, initial=u""),

    ParameterDetails(
        'WORK_ORDER_NOTICE',
        _('Work order'),
        _('Notice that will be added to the work order report'),
        _('This notice will be added to the work order receipt and can be used to '
          'warn the client about warranties and limitations'),
        str, multiline=True, initial=''),

    ParameterDetails(
        'AUTOMATIC_LOGOUT',
        _('General'),
        _('Automatic logout after inactivity period'),
        _('Set the maximum time in minutes for the user to remain idle, before being '
          'automatically logout. \nSet to zero to disable the funcionality. '
          'Requires restart to take effect.'),
        int, initial=0),

    ParameterDetails(
        'UPDATE_PRODUCTS_COST_ON_PURCHASE',
        _('Purchase'),
        _('Automatic update of products cost when making a new purchase.'),
        _('When a new purchase is made, it\'s products cost are set to '
          'the purchase\'s items cost.'),
        bool, initial=False),

    ParameterDetails(
        'UPDATE_PRODUCT_COST_ON_COMPONENT_UPDATE',
        _('Production'),
        _('Automatic update the cost of a production product'),
        _('When the list of components is updated or the cost of a component '
          'is updated, the cost of a production product will be automatically '
          'updated'),
        bool, initial=True),

    ParameterDetails(
        'UPDATE_PRODUCT_COST_ON_PACKAGE_UPDATE',
        _('Product'),
        _('Automatic update the cost of a product'),
        _('When a package product cost is updated, the cost of the component '
          'will be automatically updated. Note that it will work only if the '
          'package has only one component.'),
        bool, initial=True),

    ParameterDetails(
        'BIRTHDAY_NOTIFICATION',
        _('General'),
        _('Client birthday notification'),
        _('Notify about clients birthdays on the current day.'),
        bool, initial=True),

    # This parameter is used for communication with stoq api and stoq link lite.
    ParameterDetails(
        'USER_HASH',
        _('General'),
        _('User hash'),
        _('This hash value is used for integration and communication with stoq api '
          'and stoq link. It will be added on ping requests, tef requests and '
          'feedbacks data sent to stoq api and on the stoq statistics data sent '
          'to stoq link lite.'),
        str, initial=uuid4().hex),

    ParameterDetails(
        'ALLOW_SAME_SELLABLE_IN_A_ROW',
        _('Inventory'),
        _('This will indicates if an assisted inventory should allow the same '
          'sellable to be read in a row'),
        _('If this parameter is not set, it wont let the user to count any '
          'sellable twice in a row when using assisted count inventory'),
        bool, initial=True),

    ParameterDetails(
        'SHOW_FULL_DATETIME_ON_RECEIVABLE',
        _('Receivable'),
        _('Show full time of the sale on receivable payments'),
        _('Beyond date, display exactly the hour and minute of the sale on the '
          'receivable payments list.'),
        bool, initial=False),

    ParameterDetails(
        'REQUIRE_PRODUCT_BRANCH_OVERRIDE',
        _('POS'),
        _('Require override for products in mobile pos'),
        _('When this is true, only products that have an override for the selected branch will be '
          'available for sale in a given branch'),
        bool, initial=False),

    ParameterDetails(
        'ALLOW_NEGATIVE_STOCK',
        _('Stock'),
        _('Enable negative stock'),
        _('When this is true, allow to decrease stock even if it becames negative.'),
        bool, initial=False),
]


class ParameterAccess(object):
    """
    API for accessing and updating system parameters
    """

    def __init__(self):
        # Mapping of details, name -> ParameterDetail
        self._details = collections.OrderedDict()
        for detail in _details:
            self.register_param(detail)

        self._values_cache = None

    # Lazy Mapping of database raw database values, name -> database value
    @property
    def _values(self):
        if self._values_cache is None:
            self._values_cache = dict(
                (p.field_name, p.field_value)
                for p in get_default_store().find(ParameterData))
        return self._values_cache

    def _create_default_values(self, store):
        """Create default values for parameters that take objects"""
        self._set_default_value(store, 'USER_HASH')
        self._set_default_method_default(store)

        self._set_cfop_default(store,
                               u"DEFAULT_SALES_CFOP",
                               u"Venda de Mercadoria Adquirida",
                               u"5.102")
        self._set_cfop_default(store,
                               u"DEFAULT_RETURN_SALES_CFOP",
                               u"Devolução de Venda de Mercadoria Adquirida",
                               u"1.202")
        self._set_cfop_default(store,
                               u"DEFAULT_RECEIVING_CFOP",
                               u"Compra para Comercializacao",
                               u"1.102")
        self._set_cfop_default(store,
                               u"DEFAULT_STOCK_DECREASE_CFOP",
                               u"Outra saída de mercadoria ou "
                               u"prestação de serviço não especificado",
                               u"5.949")
        self._set_cfop_default(store,
                               u"DEFAULT_PURCHASE_RETURN_CFOP",
                               u"Devolução de compra para comercialização",
                               u"5.202")
        self._set_delivery_default(store)
        self._set_sales_person_role_default(store)
        self._set_product_tax_constant_default(store)

    def _set_default_method_default(self, store):
        from stoqlib.domain.payment.method import PaymentMethod
        if self.has_object("DEFAULT_PAYMENT_METHOD"):
            return
        method = PaymentMethod.get_by_name(store, 'money')
        self.set_object(store, u"DEFAULT_PAYMENT_METHOD", method)

    def _set_cfop_default(self, store, param_name, description, code):
        from stoqlib.domain.fiscal import CfopData
        if self.has_object(param_name):
            return
        data = self.get_object(store, param_name)
        if not data:
            # There is no unique code constraint in the cfop_data table!
            data = store.find(CfopData, code=code).any()
            if data is None:
                data = CfopData(code=code, description=description,
                                store=store)
            self.set_object(store, param_name, data)

    def _set_sales_person_role_default(self, store):
        if self.has_object("DEFAULT_SALESPERSON_ROLE"):
            return
        from stoqlib.domain.person import EmployeeRole
        role = EmployeeRole.get_or_create(store, name=_('Salesperson'))
        self.set_object(store, "DEFAULT_SALESPERSON_ROLE", role)

    def _set_product_tax_constant_default(self, store):
        if self.has_object("DEFAULT_PRODUCT_TAX_CONSTANT"):
            return

        from stoqlib.domain.sellable import SellableTaxConstant
        tax_constant = SellableTaxConstant.get_by_type(TaxType.NONE, store)
        self.set_object(store, "DEFAULT_PRODUCT_TAX_CONSTANT", tax_constant)

    def _set_delivery_default(self, store):
        if self.has_object("DELIVERY_SERVICE"):
            return
        from stoqlib.domain.sellable import (Sellable,
                                             SellableTaxConstant)
        from stoqlib.domain.service import Service
        tax_constant = SellableTaxConstant.get_by_type(TaxType.SERVICE, store)
        sellable = store.find(Sellable, description=_('Delivery')).any()
        if not sellable:
            sellable = Sellable(store=store, description=_('Delivery'))
        sellable.tax_constant = tax_constant
        service = sellable.service or Service(sellable=sellable, store=store)
        self.set_object(store, "DELIVERY_SERVICE", service)

    def _verify_detail(self, field_name, expected_type=None):
        detail = self._details.get(field_name)
        if detail is None:
            raise ValueError("%s is not a valid parameter" % (field_name, ))

        if expected_type is not None and detail.type != expected_type:
            raise ValueError("%s is not a %s parameter" % (
                field_name,
                expected_type.__name__))
        return detail

    def _set_param_internal(self, store, param_name, value, expected_type):
        self._verify_detail(param_name, expected_type)
        param = ParameterData.get_or_create(store, field_name=str(param_name))

        if value is not None and not isinstance(value, expected_type):
            raise TypeError("%s must be a %s, not %r" % (
                param_name, expected_type, type(value).__name__))

        # bool are represented as 1/0
        if expected_type is bool:
            value = int(value)

        param.field_value = str(value)
        self.set_value_generic(param_name, param.field_value)

    def _set_default_value(self, store, param_name):
        """Sets the default initial value for a param in the database

        If the param is not present in the ParameterData table, it will be
        created with the default initial value.
        """
        if self._values.get(param_name, None) is not None:
            return

        detail = self.get_detail_by_name(param_name)
        value = detail.initial
        if value is None:
            return

        if detail.type is bool:
            value = int(value)
        if value is not None:
            value = str(value)

        data = ParameterData(store=store,
                             field_name=param_name,
                             field_value=value,
                             is_editable=detail.is_editable)
        self._values[param_name] = data.field_value
        return data.field_value

    def _remove_unused_parameters(self, store):
        """
        Remove any  parameter found in ParameterData table which is not
        used any longer.
        """
        for param_name in self._values:
            if param_name not in self._details:
                param = store.find(ParameterData,
                                   field_name=param_name).one()
                store.remove(param)

    #
    # Public API
    #

    def register_param(self, detail):
        self._details[detail.key] = detail

    def clear_cache(self):
        """Clears the internal cache so it can be rebuilt on next access"""
        self._values_cache = None

    def ensure_system_parameters(self, store, update=False):
        """
        :param update: ``True`` if we're upgrading a database,
          otherwise ``False``
        """
        # This is called when creating a new database or
        # updating an existing one

        # Clear cached values to ensure the parameters updates
        # will be used correctly. If there any change in name, these values
        # will differ from database.
        if update:
            self.clear_cache()
        self._create_default_values(store)

    def get(self, param_name, expected_type=None, store=None):
        detail = self._verify_detail(param_name, expected_type)
        value = self._values.get(param_name)
        if value is None:
            # This parameter should be created on read and not on edit.
            if param_name == 'USER_HASH':
                from stoqlib.database.runtime import new_store
                new_store = new_store()
                value = self._set_default_value(new_store, 'USER_HASH')
                new_store.commit()
                return value
            # initial value is already of the correct type
            return detail.initial

        if expected_type is bool:
            return value == '1'
        elif expected_type in (Decimal, int):
            try:
                return expected_type(value)
            except ValueError:
                return expected_type(detail.initial)
        elif isinstance(expected_type, str):
            field_type = detail.get_parameter_type()
            return store.get(field_type, str(value))

        return value

    def set_bool(self, store, param_name, value):
        """
        Updates a database bool value for a given parameter.

        :param store: a database store
        :param param_name: the parameter name
        :param value: the value to set
        :type value: bool
        """
        self._set_param_internal(store, param_name, value, bool)

    def get_bool(self, param_name):
        """
        Fetches a bool database value.

        :param param_name: the parameter name
        :returns: the database value
        :rtype: bool
        """
        return self.get(param_name, bool)

    def set_decimal(self, store, param_name, value):
        """
        Updates a database decimal value for a given parameter.

        :param store: a database store
        :param param_name: the parameter name
        :param value: the value to set
        :type value: decimal.Decimal
        """
        self._set_param_internal(store, param_name, value, Decimal)

    def get_decimal(self, param_name):
        """
        Fetches a decimal database value.

        :param param_name: the parameter name
        :returns: the database value
        :rtype: decimal.Decimal
        """
        return self.get(param_name, Decimal)

    def set_int(self, store, param_name, value):
        """
        Updates a database int value for a given parameter.

        :param store: a database store
        :param param_name: the parameter name
        :param value: the value to set
        :type value: int
        """
        self._set_param_internal(store, param_name, value, int)

    def get_int(self, param_name):
        """
        Fetches an int database value.

        :param param_name: the parameter name
        :returns: the database value
        :rtype: int
        """
        return self.get(param_name, int)

    def set_string(self, store, param_name, value):
        """
        Updates a database unicode value for a given parameter.

        :param store: a database store
        :param param_name: the parameter name
        :param value: the value to set
        :type value: unicode
        """
        self._set_param_internal(store, param_name, str(value or ''), str)

    def get_string(self, param_name):
        """
        Fetches a unicode database value.

        :param param_name: the parameter name
        :returns: the database value
        :rtype: unicode
        """
        return self.get(param_name, str)

    def set_object(self, store, param_name, value):
        """
        Updates a database object.

        :param store: a database store
        :param param_name: the parameter name
        :param value: the value to set
        :type value: a domain object
        """
        detail = self._details.get(param_name)
        if detail is None:
            raise ValueError("%s is not a valid parameter" % (param_name, ))

        field_type = detail.get_parameter_type()
        if (value is not None and
                not isinstance(value, field_type)):
            raise TypeError("%s must be a %s instance, not %r" % (
                param_name, field_type.__name__,
                type(value).__name__))

        param = ParameterData.get_or_create(store, field_name=str(param_name))
        if value is not None:
            value = str(value.id)
        param.field_value = value
        param.is_editable = detail.is_editable
        self._values[param_name] = value

    def get_object(self, store, param_name):
        """
        Fetches an object from the database.

        ..note..:: This has to query the database to build an object and
                   it is slower than other getters, avoid it if you can.

        :param store: a database store
        :param param_name: the parameter name
        :returns: the object
        """
        detail = self._verify_detail(param_name)
        return self.get(param_name, detail.type, store)

    def get_object_id(self, param_name):
        """
        Fetches the database object id

        :param param_name: the parameter name
        :returns: the object id
        """
        return self.get(param_name)

    def has_object(self, param_name):
        """
        Check if an object is set.

        :param param_name: the parameter name
        """
        value = self.get(param_name)
        return value is not None

    def compare_object(self, param_name, other_object):
        """
        Compare the currently set value of a parameter with
        a specified object.

        :param param_name: the parameter name
        :param other_object: object to compare
        """
        object_id = self.get(param_name)
        if object_id is None and other_object is None:
            return True
        if other_object is None:
            return False

        # FIXME: Enable this type checking in the future
        # if type(other_object) != detail.get_parameter_type():
        #     raise TypeError("Expected an object of type %s, but got a %s" % (
        #         detail.get_parameter_type().__name__,
        #         type(other_object).__name__))
        return object_id == other_object.id

    def set_value_generic(self, param_name, value):
        """Update the internal cache for a parameter

        :param param_name: the parameter name
        :param value: value
        :type value: unicode
        """
        # FIXME: Find a better way of doing this after we integrate stoq.link
        # better with Stoq.
        if param_name == 'ONLINE_SERVICES':
            from stoqlib.lib.threadutils import threadit
            from stoqlib.net.server import ServerProxy
            p = ServerProxy(timeout=5)
            threadit(lambda: p.check_running() and p.call('restart'))

        self._values[param_name] = value

    def get_details(self):
        return list(self._details.values())

    def get_detail_by_name(self, param_name):
        """
        Returns a ParameterDetails class for the given parameter name

        :param param_name: the parameter name
        :returns: the detail
        """
        detail = self._details.get(param_name)
        if detail is None:
            raise KeyError("Unknown parameter: %r" % (param_name, ))
        return detail


sysparam = ParameterAccess()
