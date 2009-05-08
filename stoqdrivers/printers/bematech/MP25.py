# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Cleber Rodrigues      <cleber@globalred.com.br>
##              Henrique Romano       <henrique@async.com.br>
##              Johan Dahlin          <jdahlin@async.com.br>
##              Ronaldo Maia          <romaia@async.com.br>
##
"""
Bematech MP25 driver
"""

import datetime
from decimal import Decimal
import struct

from kiwi.log import Logger
from kiwi.python import Settable
from zope.interface import implements

from stoqdrivers.serialbase import SerialBase
from stoqdrivers.exceptions import (DriverError, OutofPaperError, PrinterError,
                                    CommandError, CouponOpenError,
                                    HardwareFailure,
                                    PrinterOfflineError, PaymentAdditionError,
                                    ItemAdditionError, CancelItemError,
                                    CouponTotalizeError, CouponNotOpenError)
from stoqdrivers.interfaces import ICouponPrinter
from stoqdrivers.printers.capabilities import Capability
from stoqdrivers.printers.base import BaseDriverConstants
from stoqdrivers.enum import TaxType, UnitType
from stoqdrivers.translation import stoqdrivers_gettext

_ = stoqdrivers_gettext

log = Logger('stoqdrivers.bematech.MP25')

CASH_IN_TYPE = "SU"
CASH_OUT_TYPE = "SA"

# The comment after the commands are comparing the MP25 command with MP20.

CMD_COUPON_OPEN = 0 # MP25 aceita 2 parametros opcionais a mais
CMD_CLOSE_TILL = 5
CMD_REDUCE_Z = 5
CMD_READ_X = 6
CMD_READ_MEMORY = 8
CMD_COUPON_CANCEL = 14 # MP25 aceita 3 parametros opicionais
CMD_STATUS = 19
CMD_ADD_VOUCHER = 25
CMD_READ_TAXCODES = 26
CMD_READ_TOTALIZERS = 27
CMD_GET_COUPON_SUBTOTAL = 29
CMD_GET_COUPON_NUMBER = 30
CMD_CANCEL_ITEM = 31
CMD_COUPON_TOTALIZE = 32 # MP 20 Nao permite desconto simultaneo
CMD_COUPON_CLOSE = 34
CMD_READ_REGISTER = 35 # Registradores diferentes
CMD_ADD_ITEM = 63
CMD_PAYMENT_RECEIPT_OPEN = 66 # MP20 suporta somente 3 primeiro parametros
CMD_PAYMENT_RECEIPT_PRINT = 67
CMD_PAYMENT_RECEIPT_CLOSE = 21 # Parece o mesmo, mas com nomes diferentes na mp20 e 25
CMD_PROGRAM_PAYMENT_METHOD = 71
CMD_ADD_PAYMENT = 72
# Be carefull with these commands, They are only available for MP25 (not mp20)
CMD_CANCEL_LAST = 81
CMD_PAYMENT_RECEIPT_PRINT_DUPLICATE = 91


NAK = 21
ACK = 6
STX = 2

RETRIES_BEFORE_TIMEOUT = 5

# Page 51
class MP25Registers(object):
    TOTAL = 3
    TOTAL_CANCELATIONS = 4
    TOTAL_DISCOUNT = 5
    COO = 6
    GNF = 7
    NUMBER_REDUCTIONS_Z = 9
    CRO = 10
    LAST_ITEM_ID = 12
    NUMBER_TILL = 14
    EMISSION_DATE = 23
    TOTALIZERS = 29
    PAYMENT_METHODS = 32
    SERIAL = 40
    FIRMWARE = 41
    CCF = 55

    # (size, bcd)
    formats = {
        TOTAL: ('9s', True),
        TOTAL_CANCELATIONS: ('7s', True),
        TOTAL_DISCOUNT: ('7s', True),
        COO: ('3s', True),
        GNF: ('3s', True),
        NUMBER_REDUCTIONS_Z: ('2s', True),
        CRO: ('2s', True),
        LAST_ITEM_ID: ('2s', True),
        NUMBER_TILL: ('2s', True),
        EMISSION_DATE: ('6s', False),
        TOTALIZERS: ('2s', False),
        #  1 + (52 * 16) + (52 * 10) + (52 * 10) + (52 * 1)
        #  1 + 832 + 520 + 520 + 52: 1925
        PAYMENT_METHODS: ('b832s520s520s52s', False),
        SERIAL: ('20s', False),
        FIRMWARE: ('3s', True),
        CCF: ('3s', True),
    }


class MP25Constants(BaseDriverConstants):
    _constants = {
        UnitType.WEIGHT:      'Kg',
        UnitType.METERS:      'm ',
        UnitType.LITERS:      'Lt',
        UnitType.EMPTY:       '  ',
        }


class MP25Status(object):
    st1_codes = {
        128: (OutofPaperError(_("Printer is out of paper"))),
        # 64: (AlmostOutofPaper(_("Printer almost out of paper"))),
        32: (PrinterError(_("Printer clock error"))),
        16: (PrinterError(_("Printer in error state"))),
        8: (CommandError(_("First data value in CMD is not ESC (1BH)"))),
        4: (CommandError(_("Nonexistent command"))),
        # 2: (CouponOpenError(_("Printer has a coupon currently open"))),
        1: (CommandError(_("Invalid number of parameters")))}

    st2_codes = {
        128: (CommandError(_("Invalid CMD parameter"))),
        64: (HardwareFailure(_("Fiscal memory is full"))),
        32: (HardwareFailure(_("Error in CMOS memory"))),
        16: (PrinterError(_("Given tax is not programmed on the printer"))),
        8: (DriverError(_("No available tax slot"))),
        4: (CancelItemError(_("The item wasn't added in the coupon or can't "
                              "be cancelled"))),

        # 2: (PrinterError(_("Owner data (CGC/IE) not programmed on the printer"))),
        # FIXME: This shouldn't be commented. But it will break the tests.
        # Need to update the tests for all bematech printers
        #1: (CommandError(_("Command not executed")))
        }

    st3_codes = {
        # 7: (CouponOpenError(_("Coupon already Open"))),
        # 8: (CouponNotOpenError(_("Coupon is closed"))),
        13: (PrinterOfflineError(_("Printer is offline"))),
        16: (DriverError(_("Surcharge or discount greater than coupon total"
                           "value"))),
        17: (DriverError(_("Coupon with no items"))),
        20: (PaymentAdditionError(_("Payment method not recognized"))),
        22: (PaymentAdditionError(_("Isn't possible add more payments since"
                                     "the coupon total value already was "
                                    "reached"))),
        23: (DriverError(_("Coupon isn't totalized yet"))),
        43: (CouponNotOpenError(_("Printer not initialized"))),
        45: (PrinterError(_("Printer without serial number"))),
        52: (DriverError(_("Invalid start date"))),
        53: (DriverError(_("Invalid final date"))),
        85: (DriverError(_("Sale with null value"))),
        91: (ItemAdditionError(_("Surcharge or discount greater than item"
                                 "value"))),
        100: (DriverError(_("Invalid date"))),
        115: (CancelItemError(_("Item doesn't exists or already was cancelled"))),
        118: (DriverError(_("Surcharge greater than item value"))),
        119: (DriverError(_("Discount greater than item value"))),
        129: (CouponOpenError(_("Invalid month"))),
        169: (CouponTotalizeError(_("Coupon already totalized"))),
        170: (PaymentAdditionError(_("Coupon not totalized yet"))),
        171: (DriverError(_("Surcharge on subtotal already effected"))),
        172: (DriverError(_("Discount on subtotal already effected"))),
        176: (DriverError(_("Invalid date")))}

    def __init__(self, reply):
        self.st1, self.st2, self.st3 = reply[-3:]

    @property
    def open(self):
        return self.st1 & 2

    def _check_error_in_dict(self, error_codes, value):
        for key in error_codes:
            if key & value:
                raise error_codes[key]

    def check_error(self):
        log.debug("status: st1=%s st2=%s st3=%s" %
                    (self.st1, self.st2, self.st3))

        if self.st1 != 0:
            self._check_error_in_dict(self.st1_codes, self.st1)

        if self.st2 != 0:
            self._check_error_in_dict(self.st2_codes, self.st2)

            # first bit means not executed, look in st3 for more
            if self.st2 & 1 and self.st3:
                if self.st3 in self.st3_codes:
                    raise self.st3_codes[self.st3]


#
# Helper functions
#

def bcd2dec(data):
    return int(''.join(['%02x' % ord(i) for i in data]))

def bcd2hex(data):
    return ''.join(['%02x' % ord(i) for i in data])

def dec2bcd(dec):
    return chr(dec % 10 + (dec / 10) * 16)

def dec2bin(n, trim=-1):
    a = ""
    while n > 0:
        if n % 2 == 0:
            a = "0" + a
        else:
            a = "1" + a
        n /= 2

    if trim != -1:
        if len(a) < trim:
            a = ("0" * (trim-len(a))) + a
    return a

#
# Driver implementation
#

class MP25(SerialBase):
    implements(ICouponPrinter)
    CMD_PROTO = 0x1c

    supported = True
    model_name = "Bematech MP25 FI"
    coupon_printer_charset = "cp850"
    supports_duplicate_receipt = True
    identify_customer_at_end = False
    registers = MP25Registers
    reply_format = '<b%sbbH'
    status_size = 3

    EOL_DELIMIT = '\n'

    def __init__(self, port, consts=None):
        self._consts = consts or MP25Constants
        port.set_options(read_timeout=2, write_timeout=5)
        SerialBase.__init__(self, port)
        # XXX: Seems that Bematech doesn't contains any variable with the
        # coupon remainder value, so I need to manage it by myself.
        self.remainder_value = Decimal("0.00")
        self._reset()

    def _reset(self):
        self._customer_name = ''
        self._customer_document = ''
        self._customer_address = ''

    def _create_packet(self, command):
        """
        Create a 'pre-package' (command + params, basically) and involves
        it around STX, NB and CS::
           1     2           n           2
        +-----+------+-----------------+----+
        | STX |  NB  | 0x1C + command  | CS |
        +-----+------+-----------------+----+

        Where:

        STX: 'Transmission Start' indicator byte
        NB: 2 bytes, big endian length of command + CS (2 bytes)
        CS: 2 bytes, big endian checksum for command
        """

        command = chr(self.CMD_PROTO) + command
        return struct.pack('<bH%dsH' % len(command),
                           STX,
                           len(command) + 2,
                           command,
                           sum([ord(i) for i in command]))

    def _read_reply(self, size):
        a = 0
        data = ''
        while True:
            if a > RETRIES_BEFORE_TIMEOUT:
                raise DriverError("Timeout")

            a += 1
            reply = self.read(size)
            if reply is None:
                continue

            data += reply
            if len(data) < size:
                continue

            log.debug("<<< %r (%d bytes)" % (data, len(data)))
            return data

    def _check_error(self, retval=None):
        status = self.get_status(retval)
        status.check_error()

    def _send_command(self, command, *args, **kwargs):
        fmt = ''
        if 'response' in kwargs:
            fmt = kwargs.pop('response')

        raw = False
        if 'raw' in kwargs:
            raw = kwargs.pop('raw')

        if kwargs:
            raise TypeError("Invalid kwargs: %r" % (kwargs,))

        cmd = chr(command)
        for arg in args:
            if isinstance(arg, int):
                cmd += chr(arg)
            elif isinstance(arg, str):
                cmd += arg
            else:
                raise NotImplementedError(type(arg))

        data = self._create_packet(cmd)
        self.write(data)

        format = self.reply_format % fmt
        reply = self._read_reply(struct.calcsize(format))
        retval = struct.unpack(format, reply)

        if raw:
            return retval

        self._check_error(retval)

        response = retval[1:-self.status_size]
        if len(response) == 1:
            response = response[0]
        return response

    def _read_register(self, reg):
        try:
            fmt, bcd = self.registers.formats[reg]
        except KeyError:
            raise NotImplementedError(reg)

        value = self._send_command(CMD_READ_REGISTER, reg, response=fmt)
        if bcd:
            value = bcd2dec(value)
        return value

    #
    # Helper methods
    #

    def _get_coupon_subtotal(self):
        subtotal = self._send_command(CMD_GET_COUPON_SUBTOTAL, response='7s')
        if subtotal:
            return Decimal(bcd2dec(subtotal)) / Decimal("1e2")
        # Busted subtotal
        return Decimal("0.0")

    def _get_last_item_id(self):
        return self._read_register(self.registers.LAST_ITEM_ID)

    def _get_coupon_number(self):
        coupon_number = self._send_command(CMD_GET_COUPON_NUMBER, response='3s')
        return bcd2dec(coupon_number)

    def get_status(self, val=None):
        if val is None:
            val = self._send_command(CMD_STATUS, raw=True)

        return MP25Status(val)

    def _add_voucher(self, type, value):
        assert len(type) == 2

        status = self.get_status()
        if status.open:
            self._send_command(CMD_COUPON_CANCEL)

        self._send_command(CMD_ADD_VOUCHER, type, "%014d" % int(value * Decimal('1e2')))

    def _configure_payment_methods(self):
        # Do one at a time, if you need it.
        ret = self._send_command(CMD_PROGRAM_PAYMENT_METHOD,
                                 '%-16s1' % 'Cartao Credito', raw=True)
        #ret = self._send_command(CMD_PROGRAM_PAYMENT_METHOD,
        #                         '%-16s1' % 'Cartao Debito', raw=True)
        #ret = self._send_command(CMD_PROGRAM_PAYMENT_METHOD,
        #                         '%-16s1' % 'Cheque', raw=True)

    #
    # This implements the ICouponPrinter Interface
    #

    def summarize(self):
        """ Prints a summary of all sales of the day """
        self._send_command(CMD_READ_X)

    def close_till(self, previous_day=False):
        """ Close the till for the day, no other actions can be done after this
        is called.
        """
        # a impressao da Leitura X precisa ser feita diariamente. Ao utilizar o
        # parâmetro previous_day a Leitura X só será impressa quando o caixa
        # não é fechado no mesmo dia
        self._send_command(CMD_REDUCE_Z)

    def till_add_cash(self, value):
        self._add_voucher(CASH_IN_TYPE, value)

    def till_remove_cash(self, value):
        self._add_voucher(CASH_OUT_TYPE,value)

    def till_read_memory(self, start, end):
        self._send_command(CMD_READ_MEMORY,
                           '%s%sI' % (start.strftime('%d%m%y'),
                                      end.strftime('%d%m%y')))

    def _till_read_memory_to_serial(self, start, end):
        ret = self._send_command(CMD_READ_MEMORY,
                           '%s%sR' % (start.strftime('%d%m%y'),
                                      end.strftime('%d%m%y')))

        data = ''
        while True:
            c = self.read(1)
            if ord(c) == 0x03:
                break

            data += unicode(c, self.coupon_printer_charset)

        return data

    def till_read_memory_by_reductions(self, start, end):
        self._send_command(CMD_READ_MEMORY,
                           '%06d%06dI' % (start, end))

    def coupon_identify_customer(self, customer, address, document):
        self._customer_name = customer
        self._customer_document = document
        self._customer_address = address

    def coupon_is_customer_identified(self):
        return len(self._customer_document) > 0

    def coupon_open(self):
        """ This needs to be called before anything else """
        self._send_command(CMD_COUPON_OPEN,
                            "%-29s%-30s%-80s" % (self._customer_document,
                                                 self._customer_name,
                                                 self._customer_address))

    def coupon_cancel(self):
        """ Can only be called when a coupon is opened. It needs to be possible
        to open new coupons after this is called.
        """
        self._send_command(CMD_COUPON_CANCEL)

    def cancel_last_coupon(self):
        """Cancel the last non fiscal coupon or the last sale."""
        self._send_command(CMD_CANCEL_LAST)

    def coupon_close(self, message=""):
        """  This can only be called when the coupon is open, has items added,
        payments added and totalized is called. It needs to be possible to open
        new coupons after this is called.
        """
        # FIXME This will break the drivers recorded tests. Record new ones.
        #self._send_command(CMD_COUPON_CLOSE, message)
        self._send_command(CMD_COUPON_CLOSE)
        self._reset()
        return self._get_coupon_number()

    def coupon_add_item(self, code, description, price, taxcode,
                        quantity=Decimal("1.0"), unit=UnitType.EMPTY,
                        discount=Decimal("0.0"), markup=Decimal("0.0"),
                        unit_desc=""):
        if unit == UnitType.CUSTOM:
            unit = unit_desc
        else:
            unit = self._consts.get_value(unit)

        data = ("%02s"     # taxcode
                "%09d"     # value
                "%07d"     # quantity
                "%010d"    # discount
                "%010d"    # markup
                "%022d"    # padding
                "%2s"      # unit
                "%-48s\0"  # code
                "%-200s\0" # description
                % (taxcode,
                   price * Decimal("1e3"),
                   quantity * Decimal("1e3"),
                   discount * Decimal("1e2"),
                   markup * Decimal("1e2"),
                   0, unit, code, description))
        self._send_command(CMD_ADD_ITEM, data)
        return self._get_last_item_id()

    def coupon_cancel_item(self, item_id=None):
        """ Cancel an item added to coupon; if no item id is specified,
        cancel the last item added. """
        last_item = self._get_last_item_id()
        if item_id is None:
            item_id = last_item
        elif item_id not in xrange(1, last_item+2):
            raise CancelItemError("There is no such item with ID %r"
                                  % item_id)
        self._send_command(CMD_CANCEL_ITEM, "%04d" % (item_id,))

    def coupon_add_payment(self, payment_method, value, description=u""):
        self._send_command(CMD_ADD_PAYMENT,
                           "%s%014d%s" % (payment_method[:2],
                                          int(value * Decimal('1e2')),
                                          description[:80]))
        self.remainder_value -= value
        if self.remainder_value < 0.0:
            self.remainder_value = Decimal("0.0")
        return self.remainder_value

    def coupon_totalize(self, discount=Decimal("0.0"), markup=Decimal("0.0"),
                        taxcode=TaxType.NONE):

        if discount:
            type = 'D'
            value = discount
        elif markup:
            type = 'A'
            value = markup
        else:
            # Just to use the StartClosingCoupon in case of no discount/markup
            # be specified.
            type = 'A'
            value = 0

        self._send_command(CMD_COUPON_TOTALIZE, '%c%04d' % (
            type, int(value * Decimal('1e2'))))

        totalized_value = self._get_coupon_subtotal()
        self.remainder_value = totalized_value
        return totalized_value

    def get_payment_receipt_identifier(self, method):
        # We don't need one.
        return None

    def _get_payment_description(self, method_id):
        constants = self.get_payment_constants()
        for value, name in constants:
            if value == method_id:
                return name

    def payment_receipt_open(self, identifier, coo, method_id, value):
        method = self._get_payment_description(method_id)
        if not method:
            raise DriverError('Looks like this payment method '
                              'is not configured in the printer')

        value = int(value*100)
        self._send_command(CMD_PAYMENT_RECEIPT_OPEN,
                           '%-16s%014d%06d' % (method, value, coo))

    def payment_receipt_print(self, text):
        for line in text.split('\n'):
            self._send_command(CMD_PAYMENT_RECEIPT_PRINT, line + '\n')

    def payment_receipt_close(self):
        ret = self._send_command(CMD_PAYMENT_RECEIPT_CLOSE)

    def payment_receipt_print_duplicate(self):
        self._send_command(CMD_PAYMENT_RECEIPT_PRINT_DUPLICATE)

    def get_capabilities(self):
        return dict(
            item_code=Capability(max_len=13),
            item_id=Capability(digits=4),
            items_quantity=Capability(min_size=1, digits=4, decimals=3),
            item_price=Capability(digits=6, decimals=2),
            item_description=Capability(max_len=29),
            payment_value=Capability(digits=12, decimals=2),
            promotional_message=Capability(max_len=320),
            payment_description=Capability(max_len=48),
            customer_name=Capability(max_len=30),
            customer_id=Capability(max_len=28),
            customer_address=Capability(max_len=80),
            add_cash_value=Capability(min_size=0.1, digits=12, decimals=2),
            remove_cash_value=Capability(min_size=0.1, digits=12, decimals=2),
            )

    def get_constants(self):
        return self._consts

    def query_status(self):
        #return '\x02\x05\x00\x1b#(f\x00'
        query = self._create_packet(chr(CMD_READ_REGISTER) +
                                    chr(self.registers.SERIAL))
        return query

    def status_reply_complete(self, reply):
        return len(reply) == 25

    def get_serial(self):
        return self._read_register(self.registers.SERIAL).strip('\x00')

    def get_ccf(self):
        return self._read_register(self.registers.CCF)

    def get_coo(self):
        return self._read_register(self.registers.COO)

    def get_gnf(self):
        return self._read_register(self.registers.GNF)

    def get_crz(self):
        return self._read_register(self.registers.NUMBER_REDUCTIONS_Z)

    def get_tax_constants(self):
        status = self._read_register(self.registers.TOTALIZERS)
        status = struct.unpack('>H', status)[0]

        length, data = self._send_command(CMD_READ_TAXCODES, response='b32s')

        service = False
        constants = []
        for i in range(16):
            value = bcd2dec(data[i*2:i*2+2])
            if not value:
                continue

            if 1 << 15-i & status == 0:
                tax = TaxType.CUSTOM
            else:
                tax = TaxType.SERVICE
            constants.append((tax,
                              '%02d' % (i+1,),
                              Decimal(value) / 100))

        constants.extend([
            (TaxType.SUBSTITUTION, 'FF', None),
            (TaxType.EXEMPTION,    'II', None),
            (TaxType.NONE,         'NN', None),
            ])

        return constants

    def get_payment_constants(self):
        status = self._read_register(self.registers.PAYMENT_METHODS)[1]
        methods = []
        for i in range(20):
            method = status[i*16:i*16+16]
            if method != '\x00' * 16:
                methods.append(('%02d' % (i+1), method.strip()))
        return methods

    def get_sintegra(self):
        opening_date = self._read_register(self.registers.EMISSION_DATE)
        cro = self._read_register(self.registers.CRO)
        # FIXME: This is being fetched before the actual reduction, so the value will be wrong by
        # -1
        crz = self._read_register(self.registers.NUMBER_REDUCTIONS_Z)
        coo = self._get_coupon_number()
        total_cancelations = self._read_register(self.registers.TOTAL_CANCELATIONS)
        total_discount = self._read_register(self.registers.TOTAL_DISCOUNT)

        # Avbr function TACBrECFBematech.GetVendaBruta
        registers = self._send_command(62 , 55, response='308s')
        coupon_end = int(bcd2hex(registers)[568:568+6])

        grande_total = self._read_register(self.registers.TOTAL)
        grande_total = grande_total/Decimal(100)
        total_bruto = bcd2dec(registers[1:10])/Decimal(100)

        length, names = self._send_command(CMD_READ_TAXCODES, response='b32s')
        status = self._read_register(self.registers.TOTALIZERS)
        status = struct.unpack('>H', status)[0]
        values = self._send_command(CMD_READ_TOTALIZERS, response='219s')

        taxes = []
        for i in range(length):
            if 1 << 15-i & status != 0:
                type = 'ISS'
            else:
                type = 'ICMS'

            name = bcd2hex(names[i*2:i*2+2])
            value = bcd2dec(values[i*7:i*7+7])
            taxes.append((name, value/Decimal(100), type))

        taxes.append(('CANC', total_cancelations/Decimal(100), 'ICMS'))
        taxes.append(('DESC', total_discount/Decimal(100), 'ICMS'))
        taxes.append(('I', bcd2dec(values[112:119])/Decimal(100), 'ICMS'))
        taxes.append(('N', bcd2dec(values[119:126])/Decimal(100), 'ICMS'))
        taxes.append(('F', bcd2dec(values[126:133])/Decimal(100), 'ICMS'))
        date = bcd2hex(opening_date[:6])

        return Settable(
             opening_date=datetime.date(year=2000+int(date[4:6]),
                                        month=int(date[2:4]),
                                        day=int(date[:2])),
             serial=self.get_serial(),
             serial_id='%03d' % self._read_register(self.registers.NUMBER_TILL),
             coupon_start=0,
             coupon_end=coupon_end,
             cro=cro,
             crz=crz,
             coo=coo,
             period_total=grande_total - total_bruto,
             total=grande_total,
             taxes=taxes)

    def get_firmware_version(self):
        """Return the firmware version"""
        # REGISTER IS AN INTEGER: 10000 and shoud be formated as 01.00.00
        ret = self._read_register(self.registers.FIRMWARE)
        ret = '%0*d' % (6, ret)
        firmware = "%s:%s:%s" % (ret[0:2], ret[2:4], ret[4:6])
        return firmware


    def get_user_registration_info(self):
        # http://partners.bematech.com.br/flashtip/2007/06/
        data = self._till_read_memory_to_serial(datetime.date.today(), datetime.date.today())

        pos = data.index('--------USUÁRIOS--------')
        end = data.index('----REDUÇõES DIÁRIAS----')
        data = data[pos:end].split('\n')

        user_number = 0
        cro = 0
        register_date = datetime.date.today()
        register_time = datetime.time(0,0,0)
        for i in data:
            if not i.startswith('Usuário:'):
                continue

            user_number = int(i[8:12])
            cro = int(i[20:24])

            date_parts = i[28:38].split('/')
            time_parts = i[39:].split(':')
            register_date = datetime.datetime(int(date_parts[2]),
                                              int(date_parts[1]),
                                              int(date_parts[0]),
                                              int(time_parts[0]),
                                              int(time_parts[1]))

        return Settable(
                user_number=user_number,
                register_date=register_date,
                cro=cro)
