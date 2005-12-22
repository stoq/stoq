# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
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
## Author(s):   Henrique Romano <henrique@async.com.br>
##
"""
stoqdrivers/devices/printers/dataregis/EP375.py:
    
    Dataregis 375-EP printer drivers implementation
"""

import time

from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE
from zope.interface import implements

from stoqdrivers.devices.serialbase import SerialBase
from stoqdrivers.devices.printers.interface import (IChequePrinter,
                                                    ICouponPrinter)
from stoqdrivers.exceptions import (DriverError, PendingReduceZ, PendingReadX,
                                    PrinterError, CommError, CommandError,
                                    CommandParametersError, ReduceZError,
                                    HardwareFailure, OutofPaperError)
from stoqdrivers.constants import (MONEY_PM, CHEQUE_PM, TAX_ICMS, TAX_NONE,
                                   TAX_IOF, TAX_SUBSTITUTION, TAX_EXEMPTION,
                                   UNIT_LITERS, UNIT_METERS, UNIT_WEIGHT,
                                   UNIT_EMPTY)
from stoqdrivers.devices.printers.cheque import (BaseChequePrinter,
                                                 BankConfiguration)
from stoqdrivers.devices.printers.capabilities import Capability

EOT = 0x04
BS = 0x08
ACK = 0x06
CR = 0x0D
SUB = 0x1A

#
# Class implementation to printer status management
#

class EP375Status:
    opened_drawer = None
    has_cmc7 = None
    technical_mode = None
    internal_state = None
    is_ready = None
    statuses = None

    NEEDS_REDUCE_Z = 0x4F
    NEEDS_READ_X = 0x41
    HAS_BEEN_TOTALIZED = 0x46
    PRINTER_IS_OK = 0x4B

    errors_dict = {
        0x41: (PrinterError, "Fiscal memory has changed"),
        0x61: (PrinterError, "No manufacture number"),
        0x42: (CommError, "Print buffer is full"),
        0x62: (CommandParametersError, "No item(s) to cancel found"),
        0x43: (CommandError, "The requested command doesn't exist"), 
        0x63: (DriverError, "Cancellation above the limit"),
        0x44: (DriverError, "Discount more than total value"),
        0x64: (DriverError, "Invalid date"),
        0x45: (HardwareFailure, "Fiscal EPROM disconnected"),
        0x65: (PrinterError, "Incorrect version of the basic software"),
        0x46: (PrinterError, "Error on the fiscal variables"), 
        0x66: (PrinterError, "No cliche"),
        0x47: (PrinterError, ("No company data. Has the printer been "
                              "initialized?")),
        0x67: (DriverError, "Invalid voucher amount or quantity"),
        0x48: (DriverError, "Invalid managemental report number or quantity"),
        0x68: (DriverError, "There is no more copies for the tied coupon"),
        0x49: (CommandError, "Invalid command"),
        0x69: (CommandParametersError, "Invalid command parameters"),
        0x4a: (DriverError, "Sale subjects to ICMS without state registry"),
        0x4d: (PrinterError, 'Fiscal memory without logotype'),
        0x6d: (HardwareFailure, "Write error on the Fiscal Memory"),
        0x4e: (CommandError, "Invalid state"), 
        0x6e: (DriverError, "Invalid 'finalizadora' number"), 
        0x50: (OutofPaperError, "Printer is running out of paper"),
        0x70: (HardwareFailure, "Printer hardware failure"),
        0x52: (PendingReduceZ, "Pending Reduce Z"),
        0x53: (DriverError, "Sale subjects to ISSQN without state registry."), 
        0x73: (PrinterError, ("Discount in subtotal with sale subjects to ICMS "
                              "and ISSQN isn't allowed")),
        0x54: (DriverError, "Wrong tribute index or number"),
        0x74: (DriverError, "Found the 'TOTAL' word and/or its variables"),
        0x55: (DriverError, "Invalid measurement unit"),
        0x56: (DriverError, "Total item value is greater than maximum allowed"),
        0x76: (DriverError, "Attempt to cancel coupon at zero"),
        0x77: (DriverError, "Total item value is zero"),
        0x58: (PendingReadX, "Pending Read X"), 
        0x59: (ReduceZError, "Attempt of reduce Z with date previous than last"),
        0x79: (DriverError, ("Attempt of adjust the clock to date/time previous"
                             "than the last reduce Z")),
        0x7a: (HardwareFailure, "No more fiscal memory :("),
        0x5a: (ReduceZError, "Reduce Z already done")
        }

    def __init__(self, raw_status):
        self.parse(raw_status)

    def parse_error(self):
        status = ord(self.statuses)

        # There is no error to parse.
        if status == EP375Status.PRINTER_IS_OK:
            return
        try:
            exception, reason = self.errors_dict[status]
            raise exception(reason)
        except KeyError:
            raise DriverError("Unhandled error: %d" % status)

    def needs_reduce_Z(self):
        return ord(self.internal_state) == EP375Status.NEEDS_REDUCE_Z

    def needs_read_X(self):
        return ord(self.internal_state) == EP375Status.NEEDS_READ_X

    def has_been_totalized(self):
        return ord(self.internal_state) == EP375Status.HAS_BEEN_TOTALIZED

    def parse(self, status):
        """ This method parse the result of the 'GET_STATUS' command (see
        chart below).

        Status format:

          L S N N S K
          | | | | | |
          | | | | | +--> The warning (one of items in self.errors_dict)
          | | | | +----> Has CMC7? ('S'/'N')
          | | | +------> Opened Drawer? ('S'/'N')
          | | +--------> Technical mode? ('S'/'N')
          | +----------> Printer is ready? ('S'/'N')
          +------------> Internal state (page 15)
        """

        # Getting only the status itself
        status = status[4:10]

        (self.internal_state,
         self.is_ready,
         self.technical_model,
         self.opened_drawer,
         self.has_cmc7,
         self.statuses) = status

class CouponItem:
    def __init__(self, code, description, taxcode, quantity, price, discount,
                 charge, unit):
        self.code = code
        self.description = description
        self.taxcode = taxcode
        self.quantity = quantity
        self.price = price
        self.discount = discount
        self.charge = charge
        self.unit = unit

    def get_packaged(self):
        if len(self.description) > 20:
            desc_size = 60
        else:
            desc_size = 20

        if self.discount:
            D = self.discount
        else:
            D = self.charge
            
        return ("%-16s" # code
                "%-*s" # description
                "%02s" # taxcode
                "%06d" # quantity
                "%09d" # price
                "%04d" # discount/surcharge
                "%02d" # unit
                % (self.code[:16], desc_size, self.description[:desc_size],
                   self.taxcode, int(self.quantity * 1e3),
                   int(self.price * 1e2), int(D * 1e2), self.unit))


#
# The driver implementation
#

class EP375(SerialBase, BaseChequePrinter):

    implements(ICouponPrinter, IChequePrinter)

    printer_name = "Dataregis 375 EP"

    CHEQUE_CONFIGFILE = "dataregis.ini"

    CMD_PREFIX = '\xfe'

    #
    # IChequePrinter commands specification
    #

    CMD_CHEQUE = 'U'
    CMD_PRINT_CHEQUE = 'A'

    #
    # ICouponPrinter Commands specification
    #

    CMD_READ_X = 'G'
    CMD_REDUCE_Z = 'H'
    CMD_ADD_ITEM_WITH_DISCOUNT = 'A'
    CMD_ADD_ITEM_WITH_SURCHARGE = 'w'
    CMD_GET_STATUS = 'R'
    CMD_CANCEL_COUPON = 'F'
    CMD_ADD_PAYMENT = 'D'
    CMD_ADD_PAYMENT_WITH_CHARGE = 'c'
    CMD_CANCEL_ITEM = 'b'
    CMD_GET_REMAINING_VALUE = 'C'

    payment_methods = {
        MONEY_PM : '00',
        CHEQUE_PM : '01'
        }

    unit_indicators = {
        UNIT_LITERS: 3,
        UNIT_METERS: 4,
        UNIT_WEIGHT: 0,
        UNIT_EMPTY: 2
        }

    tax_codes = {
        TAX_IOF: "00",
        TAX_ICMS: "01",
        TAX_SUBSTITUTION: "02",
        TAX_EXEMPTION: "03",
        TAX_NONE: "04"
        }

    def __init__(self, device, baudrate=9600, bytesize=EIGHTBITS,
                 parity=PARITY_NONE, stopbits=STOPBITS_ONE):
        SerialBase.__init__(self, device, baudrate=9600, bytesize=EIGHTBITS,
                            parity=PARITY_NONE, stopbits=STOPBITS_ONE)
        BaseChequePrinter.__init__(self)
        self.coupon_discount = self.coupon_charge = 0.00
        self._command_id = self._item_counter = -1
        self.items_dict = {}

        # The printer needs a little delay to shutdown/startup. Add this
        # number as a guard to make sure that the printer doesn't freeze
        # if we start up too fast.
        time.sleep(0.2)

    #
    # Helper methods
    #

    def get_next_command_id(self):
        self._command_id += 1
        return self._command_id

    def get_next_coupon_item_id(self):
        self._item_counter += 1
        return self._item_counter

    def handle_error(self, reply):
        """ This function just get the reply package and verifies if it
        contains any errors, raising the properly exception.
        """
        #
        # Managing the many data formats that the printer can returns
        #
        first_byte = ord(reply[0])

        if first_byte == ord(self.CMD_PREFIX):
            #
            # Reply format:
            #     STX+CMD_COUNTER+CMD_ID+PARAMS_SZ+PARAMS+CHKSUM+SUB+CR
            #
            # Situation: Many messages can be sended when it starts with STX,
            # its represents that the reply can't be sent in one unique package.
            # To know if a reply/message is the last message, we need verify if
            # the SUB character is in the end of the string, if so, it is the
            # last reply's package.
            #
            result = [reply]
            while not reply.endswith(chr(SUB)):
                result.append(self.readline())
            return result
        elif first_byte == ACK:
            #
            # Reply format: ACK+CR
            #
            # When ACK+CR is received the command wasn't executed.  In this
            # case, we need call get_status() and manage the reason.
            #
            self.get_status().parse_error()
        elif first_byte == EOT:
            #
            # Reply format:  EOT + CR
            # Situation: When the command doesn't need reply
            #
            result = None
        elif first_byte == BS:
            #
            # Reply format:  BS + CR
            # Situation: When the printer will send data yet -- a new
            # call to self.readline is needed in this case.
            #
            return self.readline()
        else:
            raise ValueError("Received inconsitent data")

        return result

    def get_coupon_remaining_value(self):
        #
        # reply format:
        #     STX | CMD_COUNTER | CMD_ID | PARAMS_SZ | PARAMS | CHECKSUM
        # where PARAMS is:
        #     XYYYYYYYYYYYYYYZZZ
        # with:
        #     X == 'S' if the coupon is not completely paid
        #     Y == 14 bytes representing the remaining value
        #     Z == the number of items in the coupon.
        #
        result = self.send_command(self.CMD_GET_REMAINING_VALUE)
        has_remaining_value = result[4] == 'S'
        if has_remaining_value:
            return float(result[5:19]) / 1e2
        else:
            return 0.0

    #
    # SerialBase wrappers
    #

    def writeline(self, data):
        while not self.getDSR():
            pass
        return SerialBase.writeline(self, data)

    def readline(self):
        self.setDTR()
        return SerialBase.readline(self)


    #
    # Methods implementation to printer commands and reply management
    #

    def get_command(self, command, *params):
        """ Command format:

        +---+-----------+------+---------+--------+--------+
        |STX|CMD_COUNTER|CMD_ID|PARAMS_SZ|[PARAMS]|CHECKSUM|
        +---+-----------+------+---------+--------+--------+

        Where:

        CMD_COUNTER: the counter for the respective command sent (can be 0)
        CMD_ID: the ID of the command (1 byte)
        PARAMS_SZ: the number of parameters for the command
        PARAMS: the params listing (it's optional and only is used if
          PARAMS_SZ is greater than 0)
        CHECKSUM: the sum of all the bytes, starting at CMD_ID and ending
          at the last byte of PARAMS  (or PARAMS_SZ, if no parameters was
           sent, of course).
        """
        params = ''.join(params)
        data = '%s%c%s' % (command, len(params), params)
        checksum = sum([ord(d) for d in data]) & 0xff
        package = '%c%s%c' % (self.get_next_command_id(), data, checksum)

        return package

    def send_command(self, command, *params):
        reply = self.writeline(self.get_command(command, *params))
        result = self.handle_error(reply)

        # If an exception is raised inside the handle_error method, it means
        # that occurs an error in the command execution and the rest of this
        # method must be ignored -- but, if the command was executed
        # successfully, the printer waits for a EOT byte, meaning that the
        # transmission is done.
        self.write(chr(EOT))

        return result

    def get_status(self):
        result = self.send_command(self.CMD_GET_STATUS)
        return EP375Status(result)

    #
    # ICouponPrinter implementation
    #

    def coupon_identify_customer(self, customer, address, document):
        # The printer Dataregis 375-EP doesn't supports customer
        # identification
        return

    def coupon_open(self):
        # 
        # Dataregis 375-EP doesn't need a function to open a coupon - the
        # coupon is opened when the first item is added, so simple checks
        # is done at this part.
        #
        status = self.get_status()

        if status.needs_reduce_Z():
            raise PendingReduceZ("Pending Reduce Z")

        if status.needs_read_X():
            raise PendingReadX("Pending Read X")

    def coupon_add_item(self, code, quantity, price, unit, description,
                        taxcode, discount, surcharge):

        if surcharge:
            cmd = self.CMD_ADD_ITEM_WITH_SURCHARGE
            D = surcharge
        else:
            cmd = self.CMD_ADD_ITEM_WITH_DISCOUNT
            D = discount

        #
        # A little problem here: the product code can only contain
        # alphanumeric characters if the taxcode is between 90-99, i.e, if the
        # product isn't tied to ICMS, otherwise the printer will not
        # recognizes the command.
        #
        try:
            code_num = int(code[:6])
        except ValueError:
            if taxcode == TAX_ICMS:
                raise ValueError("the item code can contains only numbers "
                                 "if the product is using ICMS")

        taxcode = EP375.tax_codes[taxcode]
        unit = EP375.unit_indicators[unit]

        item = CouponItem(code, description, taxcode, quantity, price,
                          discount, surcharge, unit)
        item_id = self.get_next_coupon_item_id()
        self.items_dict[item_id] = item

        self.send_command(cmd, item.get_packaged())
        return item_id

    def coupon_cancel_item(self, item_id):
        try:
            item = self.items_dict[item_id]
        except KeyError:
            raise CommandParametersError("You have specified an invalid "
                                         "item id to cancel!")
        self.send_command(self.CMD_CANCEL_ITEM, item.get_packaged())

    def coupon_cancel(self):
        self.send_command(self.CMD_CANCEL_COUPON)

    def coupon_totalize(self, discount, charge, taxcode):
        # The callsite must check if discount and charge are used together,
        # if so must raise an exception -- here we have a second check for
        # this.
        assert not (discount and charge)

        # Dataregis doesn't contains any functions to totalize the coupon,
        # so we need just save the discount/charge (if any) to use in the
        # add_payment calls
        self.coupon_discount, self.coupon_charge = discount, charge

        coupon_total_value = (self.get_coupon_remaining_value() + charge
                              - discount)
        return coupon_total_value

    def coupon_add_payment(self, payment_method, value, description=''):
        pm = EP375.payment_methods[payment_method]
        value = "%014d" % int(value * 1e2)

        if ((not self.get_status().has_been_totalized())
            and self.coupon_discount or self.coupon_charge):
            if self.coupon_discount:
                type = "D"
                D = self.coupon_discount
            else:
                type = "A"
                D = self.coupon_charge
            D = "%014d" % int(D * 1e2)
            self.send_command(self.CMD_ADD_PAYMENT_WITH_CHARGE, pm, value, D,
                              type)
        else:
            self.send_command(self.CMD_ADD_PAYMENT,
                              EP375.payment_methods[payment_method],
                              value)

        return self.get_coupon_remaining_value()

    def coupon_close(self, message=''):
        # XXX: Here we have a problem -- what we can do with the 'message'?
        # Maybe this driver implementation requires a change in the package,
        # adding an extra function "set_coupon_footer_message" to the API.
        # With this function this driver and all the another ones will allow
        # the "promotional_message" in the coupon.
        return

    def close_till(self):
        if not self.get_status().needs_reduce_Z():
            raise ReduceZError('Reduce Z already done')
        else:
            self.send_command(self.CMD_REDUCE_Z)

    def summarize(self):
        self.send_command(self.CMD_READ_X)

    def get_capabilities(self):
        # FIXME: As always, we have a problem here with Dataregis printer:
        # only one of the last 100 items can be cancelled, so the 'item_id'
        # capability must have what value? Probably we never will have
        # more than 100 items right now, so I just mark a FIXME here, this
        # must be fixed in the future.

        return dict(item_code=Capability(min_len=3, max_len=6),
                    item_id=Capability(digits=3),
                    items_quantity=Capability(min_size=1, digits=3, decimals=3),
                    item_price=Capability(digits=6, decimals=3),
                    item_description=Capability(max_len=60),
                    payment_value=Capability(digits=12, decimals=2),
                    promotional_message=Capability(),
                    payment_description=Capability(),
                    customer_name=Capability(),
                    customer_id=Capability(),
                    customer_address=Capability(),
                    cheque_thirdparty=Capability(max_len=50),
                    cheque_value=Capability(digits=12, decimals=2),
                    cheque_city=Capability(max_len=20))

    #
    # IChequePrinter implementation
    #

    def send_cheque_command(self, command, *params):
        reply = self.writeline(self.get_command(self.CMD_CHEQUE, command,
                                                *params))
        result = self.handle_error(reply)

        # If an exception is raised inside the handle_error method, it means
        # that occurs an error in the command execution and the rest of this
        # method must be ignored -- but, if the command was executed
        # successfully, the printer waits for a EOT byte, meaning that the
        # transmission is done.
        self.write(chr(EOT))

        return result

    def print_cheque(self, bank, value, thirdparty, city, date):
        if not isinstance(bank, BankConfiguration):
            raise TypeError("bank parameter must be a BankConfiguration instance")
        
        value = '%014d' % int(value * 1e2)
        thirdparty = '%-50s' % thirdparty[:50]
        city = "%-20s" % city[:20]
        date = date.strftime("%d%m%y")

        positions = [bank.get_y_coordinate("value"),
                     bank.get_x_coordinate("value"),
                     bank.get_y_coordinate("legal_amount"),
                     bank.get_x_coordinate("legal_amount"),
                     bank.get_y_coordinate("legal_amount2"),
                     bank.get_x_coordinate("legal_amount2"),
                     bank.get_y_coordinate("thirdparty"),
                     bank.get_x_coordinate("thirdparty"),
                     bank.get_y_coordinate("city"),
                     bank.get_x_coordinate("city")]
        positions_data = "".join(["%02d" % pos for pos in positions])

        self.send_cheque_command(self.CMD_PRINT_CHEQUE, positions_data, value,
                                 thirdparty, city, date)
