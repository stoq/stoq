# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2013 Async Open Source <http://www.async.com.br>
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
from stoqdrivers.printers.base import BasePrinter
from stoqdrivers.printers.fiscal import FiscalPrinter
from stoqdrivers.serialbase import VirtualPort, SerialPort
from stoqdrivers.enum import PaymentMethodType, UnitType, TaxType
from storm.references import Reference, ReferenceSet
from zope.interface import implementer

from stoqlib.database.properties import (BLOBCol, BoolCol, DateTimeCol,
                                         DecimalCol, EnumCol, IdCol,
                                         IntCol, UnicodeCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IActive, IDescribable
from stoqlib.exceptions import DeviceError
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


@implementer(IActive)
@implementer(IDescribable)
class ECFPrinter(Domain):
    """
    @param model:
    @param brand:
    @param device_name:
    @param device_serial:
    @param station:
    @param is_active:
    @param constants:
    @param baudrate:
    @cvar last_sale: reference for the last Sale
    @cvar last_till_entry: reference for the last TillEntry
    @cvar user_number: the current registrer user in the printer
    @cvar register_date: when the current user was registred
    @cvar register_cro: cro when the user was registred
    """

    __storm_table__ = 'ecf_printer'

    model = UnicodeCol()
    brand = UnicodeCol()
    device_name = UnicodeCol()
    device_serial = UnicodeCol()
    station_id = IdCol()
    station = Reference(station_id, 'BranchStation.id')
    is_active = BoolCol(default=True)
    baudrate = IntCol()
    last_sale_id = IdCol(default=None)
    last_sale = Reference(last_sale_id, 'Sale.id')
    last_till_entry_id = IdCol(default=None)
    last_till_entry = Reference(last_till_entry_id, 'TillEntry.id')
    user_number = IntCol(default=None)
    register_date = DateTimeCol(default=None)
    register_cro = IntCol(default=None)

    constants = ReferenceSet('id', 'DeviceConstant.printer_id')

    #
    # Public API
    #

    def create_fiscal_printer_constants(self):
        """
        Creates constants for a fiscal printer
        This can be called multiple times
        """
        # We only want to populate 'empty' objects.
        if not self.constants.find().is_empty():
            return

        store = self.store
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
                           constant_name=unicode(describe_constant(constant)),
                           constant_value=constant_value,
                           constant_enum=int(constant),
                           device_value=constants.get_value(constant, None),
                           printer=self,
                           store=store)

        for constant, device_value, value in driver.get_tax_constants():
            # FIXME: Looks like this is not used and/or is duplicating code from
            # ecfpriterdialog.py (_populate_constants)
            if constant == TaxType.CUSTOM:
                constant_name = '%0.2f %%' % value
            else:
                constant_name = describe_constant(constant)
            DeviceConstant(constant_type=DeviceConstant.TYPE_TAX,
                           constant_name=unicode(constant_name),
                           constant_value=value,
                           constant_enum=int(constant),
                           device_value=device_value,
                           printer=self,
                           store=store)

    def get_constants_by_type(self, constant_type):
        """
        Fetchs a list of constants for the current ECFPrinter object.
        @param constant_type: type of constant
        @type constant_type: :class:`DeviceConstant`
        @returns: list of constants
        """
        return self.store.find(DeviceConstant, printer=self,
                               constant_type=constant_type)

    def get_payment_constant(self, payment):
        """
        @param payment: the payment whose method we will lookup the constant
        @returns: the payment constant
        @rtype: :class:`DeviceConstant`
        """
        constant_enum = payment.method.operation.get_constant(payment)

        if constant_enum is None:
            raise AssertionError

        return self.store.find(DeviceConstant,
                               printer=self,
                               constant_type=DeviceConstant.TYPE_PAYMENT,
                               constant_enum=int(constant_enum)).one()

    def get_tax_constant_for_device(self, sellable):
        """
        Returns a tax_constant for a device
        Raises DeviceError if a constant is not found

        @param sellable: sellable which has the tax codes
        @type sellable: :class:`stoqlib.domain.sellable.Sellable`
        @returns: the tax constant
        @rtype: :class:`DeviceConstant`
        """

        sellable_constant = sellable.get_tax_constant()
        if sellable_constant is None:
            raise DeviceError("No tax constant set for sellable %r" % sellable)

        store = self.store
        if sellable_constant.tax_type == TaxType.CUSTOM:
            constant = DeviceConstant.get_custom_tax_constant(
                self, sellable_constant.tax_value, store)
            if constant is None:
                raise DeviceError(_(
                    "fiscal printer is missing a constant for the custom "
                    "tax constant '%s'") % (sellable_constant.description, ))
        else:
            constant = DeviceConstant.get_tax_constant(
                self, sellable_constant.tax_type, store)
            if constant is None:
                raise DeviceError(_(
                    "fiscal printer is missing a constant for tax "
                    "constant '%s'") % (sellable_constant.description, ))

        return constant

    def get_fiscal_driver(self):
        if self.brand == 'virtual':
            port = VirtualPort()
        else:
            port = SerialPort(device=self.device_name, baudrate=self.baudrate)
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
        # Quick workaround to avoid calling FiscalPrinter.setup(), since that
        # may send commands to the ECF, and we just need the description.
        # TODO: Improve stoqdrivers so we can get this easyer
        port = VirtualPort()
        driver = BasePrinter(brand=self.brand, model=self.model, port=port)
        return driver.get_model_name()

    @classmethod
    def get_last_document(cls, station, store):
        return store.find(cls, station=station, is_active=True).one()


@implementer(IDescribable)
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

    __storm_table__ = 'device_constant'

    constant_type = EnumCol()
    constant_name = UnicodeCol()
    constant_value = DecimalCol(default=None)
    constant_enum = IntCol(default=None)
    device_value = BLOBCol()
    printer_id = IdCol()
    printer = Reference(printer_id, 'ECFPrinter.id')

    TYPE_UNIT = u'unit'
    TYPE_TAX = u'tax'
    TYPE_PAYMENT = u'payment'

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
    def get_custom_tax_constant(cls, printer, constant_value, store):
        """
        Fetches a custom tax constant.

        @param printer: printer to fetch constants from
        @type printer: :class:`ECFPrinter`
        @param constant_enum: tax enum code
        @type constant_enum: int
        @param store: a store
        @returns: the constant
        @rtype: :class:`DeviceConstant`
        """
        return store.find(DeviceConstant,
                          printer=printer,
                          constant_type=DeviceConstant.TYPE_TAX,
                          constant_enum=int(TaxType.CUSTOM),
                          constant_value=constant_value).one()

    @classmethod
    def get_tax_constant(cls, printer, constant_enum, store):
        """
        Fetches a tax constant.
        Note that you need to use :class:`ECFPrinter.get_custom_tax_constant`
        for custom tax constants.

        @param printer: printer to fetch constants from
        @type printer: :class:`ECFPrinter`
        @param constant_enum: tax enum code
        @type constant_enum: int
        @param store: a store
        @returns: the constant
        @rtype: :class:`DeviceConstant`
        """
        if constant_enum == TaxType.CUSTOM:
            raise ValueError("Use get_custom_tax_constant for custom "
                             "tax codes")
        return store.find(DeviceConstant,
                          printer=printer,
                          constant_type=DeviceConstant.TYPE_TAX,
                          constant_enum=int(constant_enum)).one()

    def get_description(self):
        return self.constant_name


class FiscalSaleHistory(Domain):
    """Holds fiscal information about the sales.
    """
    TYPE_CPF = u'cpf'
    TYPE_CNPJ = u'cnpj'

    __storm_table__ = 'fiscal_sale_history'

    document_type = EnumCol(allow_none=False, default=TYPE_CPF)
    document = UnicodeCol(default=None)
    sale_id = IdCol()
    sale = Reference(sale_id, 'Sale.id')
    coo = IntCol(default=0)
    document_counter = IntCol(default=0)


class ECFDocumentHistory(Domain):
    """Documents emitted by the fiscal printer.

    This does not include fiscal coupons
    """
    TYPE_MEMORY_READ = u'memory-read'
    TYPE_Z_REDUCTION = u'z-reduction'
    TYPE_SUMMARY = u'summary'

    __storm_table__ = 'ecf_document_history'

    printer_id = IdCol()
    printer = Reference(printer_id, 'ECFPrinter.id')
    type = EnumCol()
    coo = IntCol(default=0)
    gnf = IntCol(default=0)
    crz = IntCol(default=None)
    emission_date = DateTimeCol(default_factory=datetime.datetime.now)
