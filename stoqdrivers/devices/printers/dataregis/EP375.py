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
Dataregis EP 275 drivers
"""

import time
from decimal import Decimal
from datetime import datetime

from zope.interface import implements

from stoqdrivers.devices.serialbase import SerialBase
from stoqdrivers.devices.interfaces import (IChequePrinter,
                                            ICouponPrinter)
from stoqdrivers.exceptions import (DriverError, PendingReduceZ, PendingReadX,
                                    PrinterError, CommError, CommandError,
                                    CommandParametersError, ReduceZError,
                                    HardwareFailure, OutofPaperError,
                                    CouponNotOpenError, CancelItemError,
                                    CouponOpenError)
from stoqdrivers.constants import (MONEY_PM, CHEQUE_PM, TAX_NONE,
                                   TAX_SUBSTITUTION, TAX_EXEMPTION,
                                   UNIT_LITERS, UNIT_METERS, UNIT_WEIGHT,
                                   UNIT_EMPTY, UNIT_CUSTOM)
from stoqdrivers.devices.printers.cheque import (BaseChequePrinter,
                                                 BankConfiguration)
from stoqdrivers.devices.printers.capabilities import Capability
from stoqdrivers.devices.printers.base import BaseDriverConstants
from stoqdrivers.translation import stoqdrivers_gettext

EOT = 0x04
BS = 0x08
ACK = 0x06
CR = 0x0D
SUB = 0x1A

_ = lambda msg: stoqdrivers_gettext(msg)

#
# Helper functions
#

def format_value(value, max_len):
    value = "%-*.02f" % (max_len, value)
    if len(value) > max_len:
        raise ValueError("The value is too big")
    return value

class EP375Constants(BaseDriverConstants):
    _constants = {
        UNIT_WEIGHT:      '00',
        UNIT_METERS:      '04',
        UNIT_LITERS:      '03',
        UNIT_EMPTY:       '02',
        MONEY_PM:         '00',
        CHEQUE_PM:        '01',
        }

    _tax_constants = [
        (TAX_SUBSTITUTION, '02', None),
        (TAX_EXEMPTION,    '03', None),
        (TAX_NONE,         '04', None),
        ]


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
    HAS_OPENED_REPORT = 0x52
    HAS_NO_FISCAL_SALE = 0x49
    HAS_FISCAL_SALE = 0x56

    errors_dict = {
        0x41: (PrinterError, _("Fiscal memory has changed")),
        0x61: (PrinterError, _("No manufacture number")),
        0x42: (CommError, _("Print buffer is full")),
        0x62: (CancelItemError, _("No item(s) to cancel found")),
        0x43: (CommandError, _("The requested command doesn't exist")),
        0x63: (DriverError, "Cancellation above the limit"),
        0x44: (DriverError, "Discount more than total value"),
        0x64: (DriverError, "Invalid date"),
        0x45: (HardwareFailure, _("Fiscal EPROM disconnected")),
        0x65: (PrinterError, _("Incorrect version of the basic software")),
        0x46: (PrinterError, _("Error on the fiscal variables")),
        0x66: (PrinterError, _("No cliche")),
        0x47: (PrinterError, _("No company data. Has the printer been "
                               "initialized?")),
        0x67: (DriverError, "Invalid voucher amount or quantity"),
        0x48: (DriverError, ("Invalid managemental report number or "
                             "quantity")),
        0x68: (DriverError, "There is no more copies for the tied coupon"),
        0x49: (CommandError, _("Invalid command")),
        0x69: (CommandParametersError, _("Invalid command parameters")),
        0x4a: (DriverError, "Sale subjects to ICMS without state registry"),
        0x4d: (PrinterError, _('Fiscal memory without logotype')),
        0x6d: (HardwareFailure, _("Write error on the Fiscal Memory")),
        0x4e: (CommandError, _("Invalid state")),
        0x6e: (DriverError, "Invalid 'finalizadora' number"),
        0x50: (OutofPaperError, _("Printer is running out of paper")),
        0x70: (HardwareFailure, _("Printer hardware failure")),
        0x52: (PendingReduceZ, _("Pending Reduce Z")),
        0x53: (DriverError, ("Sale subjects to ISSQN without state "
                             "registry.")),
        0x73: (PrinterError, _("Discount in subtotal with sale subjects to "
                               "ICMS and ISSQN isn't allowed")),
        0x54: (DriverError, "Wrong tribute index or number"),
        0x74: (DriverError, "Found the 'TOTAL' word and/or its variables"),
        0x55: (DriverError, "Invalid measurement unit"),
        0x56: (DriverError, ("Total item value is greater than maximum "
                             "allowed")),
        0x76: (DriverError, "Attempt to cancel coupon at zero"),
        0x77: (DriverError, "Total item value is zero"),
        0x58: (PendingReadX, _("Pending Read X")),
        0x59: (ReduceZError, _("Attempt of reduce Z with date previous than "
                               "last")),
        0x79: (DriverError, ("Attempt of adjust the clock to date/time "
                             "previous than the last reduce Z")),
        0x7a: (HardwareFailure, _("No more fiscal memory :(")),
        0x5a: (ReduceZError, _("Reduce Z already done"))
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


    def has_opened_sale(self):
        return (self.has_been_totalized()
                or ord(self.internal_state) in (EP375Status.HAS_NO_FISCAL_SALE,
                                                EP375Status.HAS_FISCAL_SALE))

    def has_opened_report(self):
        return ord(self.internal_state) == EP375Status.HAS_OPENED_REPORT

    def parse(self, status):
        """ This method parse the result of the 'GET_STATUS' command (see
        chart below).

        Status format::

          L S N N S K
          | | | | | |
          | | | | | +--> The warning (one of items in self.errors_dict)
          | | | | +----> Has CMC7? ('S'/'N')
          | | | +------> Opened Drawer? ('S'/'N')
          | | +--------> Technical mode? ('S'/'N')
          | +----------> Printer is ready? ('S'/'N')
          +------------> Internal state (page 15)
        """
        (self.internal_state,
         self.is_ready,
         self.technical_model,
         self.opened_drawer,
         self.has_cmc7,
         self.statuses) = status

    def __repr__(self):
        return ("<%s internal_state=%s is_ready=%r>" % (self.__class__.__name__,
                                                        self.internal_state,
                                                        self.is_ready))

class CouponItem:
    def __init__(self, code, description, taxcode, quantity, price, discount,
                 surcharge, unit):
        self.code = code
        self.description = description
        self.taxcode = taxcode
        self.quantity = quantity
        self.price = price
        self.discount = discount
        self.surcharge = surcharge
        self.unit = unit

    def get_packaged(self):
        if len(self.description) > 20:
            desc_size = 60
        else:
            desc_size = 20

        if self.discount:
            D = self.discount
        else:
            D = self.surcharge

        taxcode = self.taxcode
        quantity = int(float(self.quantity) * 1e3)
        price = int(float(self.price) * 1e2)
        D = int(float(D) * 1e2)

        return ("%-16s" # code
                "%-*s" # description
                "%02s" # taxcode
                "%06d" # quantity
                "%09d" # price
                "%04d" # discount/surcharge
                "%02s" # unit
                % (self.code[:16], desc_size, self.description[:desc_size],
                   taxcode, quantity, price, D, self.unit))


#
# The driver implementation
#

class EP375(SerialBase, BaseChequePrinter):

    implements(ICouponPrinter, IChequePrinter)

    model_name = "Dataregis 375 EP"
    cheque_printer_charset = "ascii"
    coupon_printer_charset = "ascii"

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
    CMD_ADD_ITEM_WITH_SURCHARGE = 'v'
    CMD_GET_STATUS = 'R'
    CMD_CANCEL_COUPON = 'F'
    CMD_ADD_PAYMENT = 'D'
    CMD_ADD_PAYMENT_WITH_SURCHARGE = 'c'
    CMD_CANCEL_ITEM = 'b'
    CMD_GET_REMAINING_VALUE = 'C'
    CMD_GET_FISCAL_COUNTERS = 'o'
    CMD_GERENCIAL_REPORT = 'j'
    CMD_CLOSE_GERENCIAL_REPORT = 'k'

    def __init__(self, port, consts):
        SerialBase.__init__(self, port)
        BaseChequePrinter.__init__(self)
        self._consts = consts or EP375Constants
        self.coupon_discount = Decimal("0.0")
        self.coupon_surcharge = Decimal("0.0")
        self._command_id = self._item_counter = -1
        self.items_dict = {}
        self._is_coupon_open = False

        # The printer needs a little delay to shutdown/startup. Add this
        # number as a guard to make sure that the printer doesn't freeze
        # if we start up too fast.
        time.sleep(0.2)

    #
    # Helper methods
    #

    def _get_next_command_id(self):
        self._command_id += 1
        return self._command_id

    def _get_next_coupon_item_id(self):
        self._item_counter += 1
        return self._item_counter

    def _unpack(self, package):
        if package[0] != EP375.CMD_PREFIX:
            raise ValueError("Received inconsistent data")
        n_params = ord(package[3])
        params = package[4:4+n_params]
        if len(params) != n_params:
            raise ValueError("Received inconsistent data")
        return params

    def _is_valid_package(self, package):
        # minimum package size:
        #     STX|CMD_COUNTER|CMD_ID|PARAMS_SZ|CHECKSUM => 5 bytes
        if len(package) < 5:
            return False
        try:
            params = self._unpack(package)
        except ValueError:
            return False
        cmdid = package[2]
        checksum = ord(package[4+len(params)])
        new_checksum = ord(self._get_packed(cmdid, params)[-1])
        return new_checksum == checksum

    def _get_and_parse_error(self):
        self._get_status().parse_error()

    def _parse_reply(self, reply):
        result = ""
        firstbyte = ord(reply[0])
        # When ACK+CR is received the command wasn't executed.  In this
        # case, we need call the printer status and manage the reason.
        if firstbyte == ACK:
            return self._get_and_parse_error()
        # When EOT is received, no reply is required (the printer will
        # send us nothing)
        elif firstbyte == EOT:
            return ""
        # When BS is received, the printer will send data yet, so we need
        # only executed the loop below
        elif firstbyte == BS:
            pass
        # Hmmm, if a broken package was sent we need manage this sending
        # ACK to the printer ("hey printer, you give me a broken package")
        # and so we need append the new reply in the current one and call
        # recursively this method.
        elif not self._is_valid_package(reply):
            self.write(chr(ACK))
            return self._parse_reply(reply + self.readline())
        else:
            result = self._unpack(reply)
        while True:
            lastbyte = ord(reply[-1])
            if lastbyte == SUB:
                break
            reply = self.readline()
            return result + self._parse_reply(reply)
        return result

    def _get_coupon_remaining_value(self):
        #
        # reply format:
        #     STX | CMD_COUNTER | CMD_ID | PARAMS_SZ | PARAMS | CHECKSUM
        # where PARAMS is:
        #     XYYYYYYYYYYYYYYZZZ
        # with:
        #     X == 'S' if the coupon is not completely paid
        #     Y == 14 bytes representing the remaining value
        #     Z == the number of items in the coupon.

        # We get the result already unpacked by send_command
        result = self._send_command(self.CMD_GET_REMAINING_VALUE)
        if result[0] == 'S':
            return Decimal(result[1:-3]) / Decimal("1e2")
        return Decimal("0.0")

    def _get_fiscal_counters(self):
        return self._send_command(self.CMD_GET_FISCAL_COUNTERS)

    def _get_coupon_number(self):
        result = self._get_fiscal_counters()
        return int(result[43:49])

    #
    # SerialBase wrappers
    #

    def writeline(self, data):
        while not self._port.getDSR():
            pass
        return SerialBase.writeline(self, data)

    def readline(self):
        self._port.setDTR()
        return SerialBase.readline(self)

    #
    # Methods implementation to printer commands and reply management
    #

    def _get_packed(self, command, *params):
        # Create a package for the command and its parameters. Package
        # format:
        #
        #         +---+-----------+------+---------+--------+--------+
        #NAME:    |STX|CMD_COUNTER|CMD_ID|PARAMS_SZ|[PARAMS]|CHECKSUM|
        #         +---+-----------+------+---------+--------+--------+
        #N_BYTES:   1       1         1        1        ?        1
        #
        # Where:
        #
        # CMD_COUNTER: the counter for the respective command sent (can be 0)
        # CMD_ID: the ID of the command
        # PARAMS_SZ: the number of parameters for the command
        # PARAMS: the params listing (it's optional and only is used if
        #   PARAMS_SZ is greater than 0)
        # CHECKSUM: the sum of all the bytes, starting at CMD_ID and ending
        #   at the last byte of PARAMS  (or PARAMS_SZ, if no parameters was
        #   sent, of course).
        params = ''.join(params)
        data = '%s%c%s' % (command, len(params), params)
        checksum = sum([ord(d) for d in data]) & 0xff
        package = '%c%s%c' % (self._get_next_command_id(),
                              data, checksum)
        return package

    def _send_command(self, command, *params):
        reply = self.writeline(self._get_packed(command, *params))
        result = self._parse_reply(reply)
        self.write(chr(EOT))
        return result

    def _get_status(self):
        result = self._send_command(self.CMD_GET_STATUS)
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

        status = self._get_status()

        if status.needs_reduce_Z():
            raise PendingReduceZ(_("Pending Reduce Z"))
        if status.needs_read_X():
            raise PendingReadX(_("Pending Read X"))
        if status.has_been_totalized() or self._is_coupon_open:
            raise CouponOpenError("There is a coupon opened")
        self._is_coupon_open = True

    def coupon_add_item(self, code, description, price, taxcode,
                        quantity=Decimal("1.0"), unit=UNIT_EMPTY,
                        discount=Decimal("0.0"),
                        surcharge=Decimal("0.0"), unit_desc=""):
        if not self._is_coupon_open:
            raise CouponNotOpenError("There is no coupon opened")
        if unit == UNIT_CUSTOM:
            unit = UNIT_EMPTY
        if surcharge:
            cmd = self.CMD_ADD_ITEM_WITH_SURCHARGE
            D = surcharge
        else:
            cmd = self.CMD_ADD_ITEM_WITH_DISCOUNT
            D = discount

        #
        # FIXME: The product code can only contain alphanumeric characters if
        # the taxcode is between 90-99, i.e, if the product isn't tied to ICMS,
        # otherwise the printer will not recognizes the command. Sooooo, what
        # can I do? Right now, if the product code has not only numbers, i'll
        # prefix with 0s to avoid more problems to the callsite, but my warning
        # remains *HERE*
        #
        code_num = 0
        try:
            code_num = int(code[:7])
        except ValueError:
            code = "%06d%s" % (code_num, code[7:])
        unit = self._consts.get_value(unit)
        item = CouponItem(code, description, taxcode, quantity, price,
                          discount, surcharge, unit)
        item_id = self._get_next_coupon_item_id()
        self.items_dict[item_id] = item

        self._send_command(cmd, item.get_packaged())
        return item_id

    def coupon_cancel_item(self, item_id):
        try:
            item = self.items_dict[item_id]
        except KeyError:
            raise CancelItemError(_("You have specified an invalid item id "
                                    "to cancel!"))
        self._send_command(self.CMD_CANCEL_ITEM, item.get_packaged())

    def coupon_cancel(self):
        status = self._get_status()
        if status.has_opened_sale():
            self.coupon_add_payment(MONEY_PM, self._get_coupon_remaining_value())
        elif status.has_opened_report():
            self._send_command('K')
        # We can have the "coupon state flag" set to True, but no coupon really
        # opened; and we *must* to manage this case too...
        elif self._is_coupon_open:
            return
        else:
            raise CouponNotOpenError("There is no coupon opened")
        self._send_command(self.CMD_CANCEL_COUPON)
        self._is_coupon_open = False

    def coupon_totalize(self, discount=Decimal("0.0"),
                        surcharge=Decimal("0.0"), taxcode=TAX_NONE):
        # The callsite must check if discount and charge are used together,
        # if so must raise an exception -- here we have a second check for
        # this.
        assert not (discount and surcharge)

        # Dataregis doesn't contains any functions to totalize the coupon,
        # so we need just save the discount/surcharge (if any) to use in the
        # add_payment calls
        coupon_subtotal = self._get_coupon_remaining_value()
        self.coupon_surcharge = coupon_subtotal * (surcharge / Decimal("100"))
        self.coupon_discount = coupon_subtotal * (discount / Decimal("100"))
        return coupon_subtotal + self.coupon_surcharge - self.coupon_discount

    def coupon_add_payment(self, payment_method, value, description='',
                           custom_pm=''):
        if not custom_pm:
            pm = self._consts.get_value(payment_method)
        else:
            pm = custom_pm
        value = "%014d" % int(float(value) * 1e2)

        if ((not self._get_status().has_been_totalized())
            and self.coupon_discount or self.coupon_surcharge):
            if self.coupon_discount:
                type = "D"
                D = self.coupon_discount
            else:
                type = "A"
                D = self.coupon_surcharge
            D = "%014d" % int(float(D) * 1e2)
            self._send_command(self.CMD_ADD_PAYMENT_WITH_SURCHARGE, pm, value,
                               D, type)
        else:
            self._send_command(self.CMD_ADD_PAYMENT, pm, value)
        return self._get_coupon_remaining_value()

    def coupon_close(self, message=''):
        # XXX: Here we have a problem -- what we can do with the 'message'?
        # Maybe this driver implementation requires a change in the package,
        # adding an extra function "set_coupon_footer_message" to the API.
        # With this function this driver and all the another ones will allow
        # the "promotional_message" in the coupon.
        self._is_coupon_open = False
        return self._get_coupon_number()

    def close_till(self):
        if not self._get_status().needs_reduce_Z():
            raise ReduceZError(_('Reduce Z already done'))
        else:
            self._send_command(self.CMD_REDUCE_Z)

    def summarize(self):
        self._send_command(self.CMD_READ_X)

    def till_add_cash(self, value):
        value = format_value(value, 32)
        self._send_command(self.CMD_GERENCIAL_REPORT, "01", "Valor = " + value)
        self._send_command(self.CMD_CLOSE_GERENCIAL_REPORT)

    def till_remove_cash(self, value):
        value = format_value(value, 32)
        self._send_command(self.CMD_GERENCIAL_REPORT, "01", "Valor = " + value)
        self._send_command(self.CMD_CLOSE_GERENCIAL_REPORT)

    def get_capabilities(self):
        # FIXME: As always, we have a problem here with Dataregis printer:
        # only one of the last 100 items can be cancelled, so the 'item_id'
        # capability must have what value? Probably we never will have
        # more than 100 items right now, so I just put a mark here, this
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
                    cheque_city=Capability(max_len=20),
                    add_cash_value=Capability(min_size=1, digits=30,
                                              decimals=2),
                    remove_cash_value=Capability(min_size=1, digits=30,
                                                 decimals=2))

    def get_constants(self):
        return self._consts

    #
    # IChequePrinter implementation
    #

    def send_cheque_command(self, command, *params):
        reply = self.writeline(self._get_packed(self.CMD_CHEQUE, command,
                                                *params))
        result = self._parse_reply(reply)
        # The printer is waiting for a 'End of Transmition' byte
        self.write(chr(EOT))
        return result

    def print_cheque(self, bank, value, thirdparty, city, date=None):
        if not isinstance(bank, BankConfiguration):
            raise TypeError("bank parameter must be a BankConfiguration "
                            "instance")
        if date is None:
            date = datetime.now()
        value = '%014d' % int(value * int(1e2))
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
