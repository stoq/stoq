# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
"""
Stoqdrivers interfaces specification
"""

from decimal import Decimal

from zope.interface import Interface, Attribute
from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE

from stoqdrivers.enum import TaxType, UnitType

__all__ = ["ISerialPort",
           "IDriverConstants",
           "IDevice",
           "ICouponPrinter",
           "IChequePrinter",
           "IScaleInfo",
           "IScale",
           ]

class ISerialPort(Interface):
    """ Interface used by drivers to write commands and get reply from devices
    """

    def getDSR():
        """ Returns True if the device is done to send data. Some drivers
        block in a loop waiting for this function returns True before call
        read.
        """

    def setDTR(value):
        """ Set to True when the driver is going to send data to the device
        """

    def set_options(baudrate=9600, bytesize=EIGHTBITS, parity=PARITY_NONE,
                    stopbits=STOPBITS_ONE, read_timeout=3, write_timeout=0):
        """ Set general device options """

    def read(n_bytes=1):
        """ Read data """

    def write(data):
        """ Write data """

class IDriverConstants(Interface):
    """ This interface determines the methods to be implemented by all objects
    that wants didacte constant values for stoqdrivers devices drivers.
    """

    def get_items():
        """ Returns all the constant identifiers which this object has
        values assigned to.
        """

    def get_value(constant):
        """ Given one of the constants defined on stoqdrivers.constants,
        returns its value.
        """

class IDevice(Interface):
    model_name = Attribute("A string describing briefly the device implemented")

class ICouponPrinter(IDevice):
    """ Describes coupon related tasks for a printer.

    Workflow::

                                    --<--                     --<--
                                   |     |                   |     |
    [identify_customer] -> open -> add_item -> totalize -> add_payment -> close
    """

    coupon_printer_charset = Attribute("The charset name which the "
                                       "coupon printer uses.")

    supports_duplicate_receipt = Attribute(
                                "Wheater or not the printer can print a "
                                "duplicate payment receipt")

    identify_customer_at_end = Attribute(
                               "True if the customer is identified at the"
                               "end of the sale. False if at the beginning")

    #
    # Common API
    #

    def coupon_identify_customer(customer, address, document):
        """ Identify the customer.  This method doesn't have mandatory
        execution (you can identify the customer only if you like), but when
        executed it must be called before calling any method.

        @param customer:
        @type customer:   str

        @param address:
        @type address:    str

        @param document:
        @type document:   str
        """

    def coupon_is_customer_identified():
        """ Returns True, if the customer have already been identified,
        False otherwise.
        """

    def coupon_open():
        """ This needs to be called before anything else (except
        identify_customer())
        """

    def coupon_add_item(code, description, price, taxcode,
                        quantity=Decimal("1.0"), unit=UnitType.EMPTY,
                        discount=Decimal("0.0"),
                        surcharge=Decimal("0.0"), unit_desc=""):
        """ Adds an item to the coupon.

        @param code:      item code identifier
        @type  code:      str

        @param description:  description of product
        @type  desription: str

        @param price:     price
        @type  price:     Decimal

        @param taxcode:   constant to descrive the tax
        @type  taxcode:   str

        @param quantity:  quantity
        @type  quantity:  Decimal

        @param unit:      constant to describe the unit
        @type unit:       integer constant one of: UnitType.LITERS, UnitType.EMPTY,
                          UnitType.METERS, UnitType.WEIGHT, UnitType.CUSTOM.

        @param discount:  discount in %
        @type  discount:  Decimal between 0-100

        @param surcharge: surcharge in %
        @type  surcharge: Decimal between 0-100

        @param unit_desc: A 2-byte string representing the unit that applies to
                          the product.
        @type unit_desc:  str

        @rtype:           Decimal
        @returns:        identifier of added item
        """

    def coupon_cancel_item(item_id):
        """ Cancels an item, item_id must be a value returned by
        coupon_add_item

        @param item_id:   the item id
        """

    def coupon_cancel():
        """
        Cancels the currently open coupon or the last closed open.
        You cannot close a previous coupon if you already created
        a new one.
        """

    def cancel_last_coupon():
        """
        Cancel the last closed non-fiscal coupon or the last sale.
        """

    def coupon_totalize(discount=Decimal("0.0"), surcharge=Decimal("0.0"),
                        taxcode=TaxType.NONE):
        """ Closes the coupon applies addition a discount or surcharge and tax.
        This can only be called when the coupon is open, has items added and
        payments added.

        @param discount:  discount in %
        @type discount:   Decimal between 0-100

        @param surcharge: surcharge in %
        @type  surcharge: Decimal between 0-100

        @param taxcode:   constant to descrive the tax
        @type  taxcode:   integer constant one of: TaxType.NONE, TaxType.SUBSTITUTION,
                          TaxType.EXEMPTION

        @rtype:           Decimal
        @returns          the coupon total value
        """

    def coupon_add_payment(payment_method, value, description=u""):
        """
        Add payment method to coupon.
        @param payment_method: The payment method.
        @type payment_method:  a device specific value representing the payment value

        @param value:     The payment value
        @type value:      Decimal

        @param description: A simple description of the payment method to be
                            appended to the coupon.
        @type value:      unicode

        @rtype:           Decimal
        @returns:         the total remaining amount
        """

    def coupon_close(message=''):
        """ It needs to be possible to open new coupons after this is called.
        You must call coupon_totalize before calling this method.

        @param message:   promotional message
        @type message:    str

        @rtype:           int
        @returns:         identifier of the coupon.
        """

    #
    # Base admin operations
    #

    def summarize():
        """ Prints a summary of all sales of the day. In Brazil this is
        'read X' operation.
        """

    def close_till(previous_day=False):
        """ Close the till for the day, no other actions can be done after
        this is called. In Brazil this is 'reduce Z' operation

        @param previous_day: if this is to close a till opened previously
        """

    def till_add_cash(value):
        """ Add an till complement. This is called 'suprimento de caixa' on
        Brazil

        @param value:     The value added
        @type value:      Decimal
        """

    def till_remove_cash(value):
        """ Retire payments from the till. This is called 'sangria' on Brazil

        @param value:     The value to remove
        @type value:      Decimal
        """

    def till_read_memory(start, end):
        """
        Reads the fiscal memory, from the date start to the date end

        @param start: start date
        @type start: datetime.date
        @param end: end date
        @type end: datetime.date
        """

    def till_read_memory_by_reductions(start, end):
        """
        Reads the fiscal memory, from the start reductions to the end
        reductions

        @param start: start reductions
        @type start: int
        @param end: end reductions
        @type end: int
        """

    def get_payment_receipt_identifier(method_name):
        """If the printer requires an identifier to open a payment receipt,
        this method should return that identifier.

        @param method_name: get receipt for specific method name.
        """

    def payment_receipt_open(identifier, coo, method, value):
        """Opens a non-fiscal bound receipt for a payment

        @param identifier: a char (A-P) representing the receipt to use.
                           The receipt must already be configured at the printer.
        @param method: another char (A-P) for the payment method. Also, this must be
                       configured at the printer. The payment method must be bindable
        @param coo: coo for the coupon containing the payment
        @param value: the value of the payment
        """

    def payment_receipt_print(text):
        """Prints the payment receipt text

        @param text: text to be printed
        """

    def payment_receipt_close():
        """Closes previouly opened payment receipt
        """

    #
    # Getting printer status
    #

    def get_capabilities():
        """ Returns a capabilities dictionary, where the keys are the strings
        below and its values are Capability instances

        * item_code           (str)
        * item_id             (int)
        * items_quantity      (float)
        * item_price          (float)
        * item_description    (str)
        * payment_value       (float)
        * payment_description (str)
        * promotional_message (str)
        * customer_name       (str)
        * customer_id         (str)
        * customer_address    (str)
        * add_cash_value      (float)
        * remove_cash_value   (float)
        """

    def get_constants():
        """ Returns the object that implements IDriverConstants where the printer
        is going to get constant values from.
        """

    def get_payment_constants():
        """"""

    def get_serial():
        """Returns the serial number for the printer"""

    def get_sintegra():
        """
        Gets an object that implements ISintegraData or None.
        """

    def get_firmware_version():
        """Firmware version of the printer
        """

    def get_ccf():
        """Fiscal Coupon Counter

        @returns: the last document ccf
        @rtype: integer
        """

    def get_coo():
        """Operation Order Counter

        @returns: the last document coo
        @rtype: integer
        """

    def get_gnf():
        """Nonfiscal Operation General Counter

        @returns: gnf
        @rtype: integer
        """

    def get_crz():
        """Z Reduction Counter

        @returns: the last document crz
        @rtype: integer
        """

    def get_user_registration_info():
        """Returns current ecf user registration date and time,
        id in the printer and cro relative to the user registration
        """

class IChequePrinter(IDevice):
    """ Interface specification for cheque printers. """

    cheque_printer_charset = Attribute("The charset name which the cheque "
                                       "printer uses.")

    def get_banks():
        """ Returns a dictionary of all banks supported by the printer. The
        dictionary's key is the bank name and its value are BankConfiguration
        instances (this classe [BankConfiguration] is used to store and manage
        the values of each section in the configuration file).
        """

    def print_cheque(bank, value, thirdparty, city, date=None):
        """ Prints a cheque

        @param bank:      the code of bank
        @type bank:       one of codes returned by get_banks method.

        @param value:     the value of the cheque
        @type value:      Decimal

        @param thirdparty: receiver of the cheque
        @type thirdparty: str

        @param city:
        @type city:       str

        @param date:      when the cheque was payed, optional
        @type date:       datetime
        """

    def get_capabilities():
        """ Returns a capabilities dictionary, where the keys are the strings
        below and its values are Capability instances

        * cheque_thirdparty   (str)
        * cheque_value        (Decimal)
        * cheque_city         (str)
        """

class IScaleInfo(Interface):
    """ This interface list the data read by the scale """
    weight = Attribute("The weight read")
    price_per_kg = Attribute("The KG read")
    total_price = Attribute("The total price. It is equivalent to "
                            "price_per_kg * weight")
    code = Attribute("The product code")

class IScale(IDevice):
    """ This interface describes how to interacts with scales.
    """

    def read_data():
        """ Read informations of the scale, returning an object
        that implements IScaleInfo interface.
        """
class IBarcodeReader(IDevice):
    """ Interface specification describing how to interacts with barcode
    readers.
    """

    def get_code():
        """ Returns the code read. Note that this function should be
        called only when there are data received (you can use
        notify_read() to be notified when data was received), or it
        will block in loop waiting the data.
        """

class ISintegraData(Interface):
    # This is used to generate a Sintegra 60M entry
    opening_date = Attribute('the day the till was opened')
    serial = Attribute('identifier of the printer')
    serial_id = Attribute('identifier of the printer, for the branch')
    coupon_start = Attribute('first coupon generated during the period')
    coupon_end = Attribute('last coupon generated during the period')
    crz = Attribute('Total number of times the till has been closed')
    cro = Attribute('Total number of times the till has been opened')
    period_total = Attribute('The value of all sales during the specified period')
    total = Attribute('The total value for all sales done by this printer')
    # This is used to generate a Sintegra 60A entry
    tax_total = Attribute('The total value including taxes')

