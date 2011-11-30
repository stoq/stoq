# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
from stoqdrivers.constants import describe_constant
from stoqdrivers.printers.fiscal import FiscalPrinter
from stoqdrivers.serialbase import VirtualPort, SerialPort
from stoqdrivers.enum import PaymentMethodType, UnitType, TaxType
from zope.interface import implements

from stoqlib.database.orm import DecimalCol
from stoqlib.database.orm import (BoolCol, StringCol, ForeignKey, IntCol,
                                  UnicodeCol, BLOBCol, DateTimeCol)
from stoqlib.database.orm import MultipleJoin
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IActive, IDescribable
from stoqlib.exceptions import DeviceError
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ECFPrinter(Domain):
    """
    @param model:
    @param brand:
    @param device_name:
    @param device_serial:
    @param station:
    @param is_active:
    @param constants:
    @cvar last_sale: reference for the last Sale
    @cvar last_till_entry: reference for the last TillEntry
    @cvar user_number: the current registrer user in the printer
    @cvar register_date: when the current user was registred
    @cvar register_cro: cro when the user was registred
    """
    implements(IActive, IDescribable)

    model = StringCol()
    brand = StringCol()
    device_name = StringCol()
    device_serial = StringCol()
    station = ForeignKey("BranchStation")
    is_active = BoolCol(default=True)
    constants = MultipleJoin('DeviceConstant')
    last_sale = ForeignKey("Sale", default=None)
    last_till_entry = ForeignKey("TillEntry", default=None)
    user_number = IntCol(default=None)
    register_date = DateTimeCol(default=None)
    register_cro = IntCol(default=None)

    #
    # Public API
    #

    def create_fiscal_printer_constants(self):
        """
        Creates constants for a fiscal printer
        This can be called multiple times
        """
        # We only want to populate 'empty' objects.
        if self.constants:
            return

        conn = self.get_connection()
        driver = self.get_fiscal_driver()
        constants = driver.get_constants()
        for constant in constants.get_items():
            constant_value = None
            if isinstance(constant, PaymentMethodType):
                constant_type = DeviceConstant.TYPE_PAYMENT
            elif isinstance(constant, UnitType):
                constant_type = DeviceConstant.TYPE_UNIT
            else:
                continue

            DeviceConstant(constant_type=constant_type,
                           constant_name=describe_constant(constant),
                           constant_value=constant_value,
                           constant_enum=int(constant),
                           device_value=constants.get_value(constant, None),
                           printer=self,
                           connection=conn)

        for constant, device_value, value in constants.get_tax_constants():
            if constant == TaxType.CUSTOM:
                constant_name = _('%d %%') % value
            else:
                constant_name = describe_constant(constant)
            DeviceConstant(constant_type=DeviceConstant.TYPE_TAX,
                           constant_name=constant_name,
                           constant_value=value,
                           constant_enum=int(constant),
                           device_value=device_value,
                           printer=self,
                           connection=conn)

    def get_constants_by_type(self, constant_type):
        """
        Fetchs a list of constants for the current ECFPrinter object.
        @param constant_type: type of constant
        @type constant_type: L{DeviceConstant}
        @returns: list of constants
        """
        return DeviceConstant.selectBy(printer=self,
                                       constant_type=constant_type,
                                       connection=self.get_connection())

    def get_payment_constant(self, payment):
        """
        @param payment: the payment whose method we will lookup the constant
        @returns: the payment constant
        @rtype: L{DeviceConstant}
        """
        constant_enum = payment.method.operation.get_constant(payment)

        if constant_enum is None:
            raise AssertionError

        return DeviceConstant.selectOneBy(
            printer=self,
            constant_type=DeviceConstant.TYPE_PAYMENT,
            constant_enum=int(constant_enum),
            connection=self.get_connection())

    def get_tax_constant_for_device(self, sellable):
        """
        Returns a tax_constant for a device
        Raises DeviceError if a constant is not found

        @param sellable: sellable which has the tax codes
        @type sellable: L{stoqlib.domain.sellable.Sellable}
        @returns: the tax constant
        @rtype: L{DeviceConstant}
        """

        sellable_constant = sellable.get_tax_constant()
        if sellable_constant is None:
            raise DeviceError("No tax constant set for sellable %r" % sellable)

        conn = self.get_connection()
        if sellable_constant.tax_type == TaxType.CUSTOM:
            constant = DeviceConstant.get_custom_tax_constant(
                self, sellable_constant.tax_value, conn)
            if constant is None:
                raise DeviceError(_(
                    "fiscal printer is missing a constant for the custom "
                    "tax constant '%s'") % (sellable_constant.description, ))
        else:
            constant = DeviceConstant.get_tax_constant(
                self, sellable_constant.tax_type, conn)
            if constant is None:
                raise DeviceError(_(
                    "fiscal printer is missing a constant for tax "
                    "constant '%s'") % (sellable_constant.description, ))

        return constant

    def get_fiscal_driver(self):
        if self.brand == 'virtual':
            port = VirtualPort()
        else:
            port = SerialPort(device=self.device_name)
        return FiscalPrinter(brand=self.brand, model=self.model, port=port)

    def set_user_info(self, user_info):
        self.user_number = user_info.user_number
        self.register_cro = user_info.cro
        self.register_date = user_info.register_date

    #
    # IActive implementation
    #

    def inactivate(self):
        self.is_active = False

    def activate(self):
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable implementation
    #

    def get_description(self):
        return '%s %s' % (self.brand.capitalize(), self.model)

    @classmethod
    def get_last_document(cls, station, conn):
        return cls.selectOneBy(station=station, is_active=True,
                               connection=conn)


class DeviceConstant(Domain):
    """
    Describes a device constant

    The constant_value field is only used by custom tax codes,
    eg when constant_type is TYPE_TAX and constant_enum is TaxType.CUSTOM

    @cvar constant_type: the type of constant
    @cvar constant_name: name of the constant
    @cvar constant_enum: enum value of the constant
    @cvar constant_value: value of the constant, only for TAX constants for
      which it represents the tax percentage
    @cvar device_value: the device value
    @cvar printer: printer
    """
    implements(IDescribable)

    constant_type = IntCol()
    constant_name = UnicodeCol()
    constant_value = DecimalCol(default=None)
    constant_enum = IntCol(default=None)
    device_value = BLOBCol()
    printer = ForeignKey("ECFPrinter")

    (TYPE_UNIT,
     TYPE_TAX,
     TYPE_PAYMENT) = range(3)

    constant_types = {TYPE_UNIT: _(u'Unit'),
                      TYPE_TAX: _(u'Tax'),
                      TYPE_PAYMENT: _(u'Payment')}

    def get_constant_type_description(self):
        """
        Describe the type in a human readable form
        @returns: description of the constant type
        @rtype: str
        """
        return DeviceConstant.constant_types[self.constant_type]

    @classmethod
    def get_custom_tax_constant(cls, printer, constant_value, conn):
        """
        Fetches a custom tax constant.

        @param printer: printer to fetch constants from
        @type printer: L{ECFPrinter}
        @param constant_enum: tax enum code
        @type constant_enum: int
        @param conn: a database connection
        @returns: the constant
        @rtype: L{DeviceConstant}
        """
        return DeviceConstant.selectOneBy(
            printer=printer,
            constant_type=DeviceConstant.TYPE_TAX,
            constant_enum=int(TaxType.CUSTOM),
            constant_value=constant_value,
            connection=conn)

    @classmethod
    def get_tax_constant(cls, printer, constant_enum, conn):
        """
        Fetches a tax constant.
        Note that you need to use L{ECFPrinter.get_custom_tax_constant}
        for custom tax constants.

        @param printer: printer to fetch constants from
        @type printer: L{ECFPrinter}
        @param constant_enum: tax enum code
        @type constant_enum: int
        @param conn: a database connection
        @returns: the constant
        @rtype: L{DeviceConstant}
        """
        if constant_enum == TaxType.CUSTOM:
            raise ValueError("Use get_custom_tax_constant for custom "
                             "tax codes")
        return DeviceConstant.selectOneBy(
            printer=printer,
            constant_type=DeviceConstant.TYPE_TAX,
            constant_enum=int(constant_enum),
            connection=conn)

    def get_description(self):
        return self.constant_name


class FiscalSaleHistory(Domain):
    """Holds fiscal information about the sales.
    """
    (TYPE_CPF,
     TYPE_CNPJ) = range(2)

    document_type = IntCol(default=TYPE_CPF)
    document = UnicodeCol(default=None)
    sale = ForeignKey('Sale')
    coo = IntCol(default=0)
    document_counter = IntCol(default=0)


class ECFDocumentHistory(Domain):
    """Documents emitted by the fiscal printer.

    This does not include fiscal coupons
    """
    (TYPE_MEMORY_READ,
     TYPE_Z_REDUCTION,
     TYPE_SUMMARY) = range(3)

    printer = ForeignKey("ECFPrinter")
    type = IntCol()
    coo = IntCol(default=0)
    gnf = IntCol(default=0)
    crz = IntCol(default=None)
    emission_date = DateTimeCol(default=datetime.datetime.now)
