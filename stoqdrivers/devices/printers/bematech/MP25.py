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
## Author(s):   Cleber Rodrigues      <cleber@globalred.com.br>
##
"""
stoqdrivers/drivers/bematech/MP25.py:
    
    Drivers implementation for Bematech printers.
"""
import struct

from zope.interface import implements

from stoqdrivers.log import Log
from stoqdrivers.devices.serialbase import SerialBase
from stoqdrivers.exceptions import (DriverError, OutofPaperError,
                                    PrinterError, CommandError,
                                    CouponOpenError, HardwareFailure,
                                    AlmostOutofPaper)
from stoqdrivers.constants import (TAX_IOF, TAX_ICMS, TAX_NONE,
                                   TAX_EXEMPTION, TAX_SUBSTITUTION,
                                   MONEY_PM, CHEQUE_PM)
from stoqdrivers.devices.printers.interface import ICouponPrinter

logger = Log(category='MP25')

# Data formatting functions
def fmt_fl_7c_3d_nodot(value):
    """Formats a float (or integer), returning a string with
    7 characters, 3 representing decimals, and with dots stripped."""
    return ('%07d' % int(float(value) * 1e3))

def fmt_fl_8c_3d_nodot(value):
    """Formats a float (or integer), returning a string with
    8 characters, 3 representing decimals, and with dots stripped."""
    return ('%08d' % int(float(value) * 1e3))

def fmt_fl_14c_2d_nodot(value):
    """Formats a float (or integer), returning a string with
    14 characters, 2 representing decimals, and with dots stripped."""
    return ('%014d' % int(float(value) * 1e2))

def fmt_st(value):
    return "%s" % value

def pretty_print_data_stream(data_stream):
    print "|".join([hex(ord(i)) for i in data_stream])

# This is broken, have to educate myself about taxes
tax_translate_dict = { TAX_IOF : "II",
                       
                       TAX_ICMS : "II",
                       TAX_SUBSTITUTION : "II",
                       TAX_EXEMPTION : "II",
                       TAX_NONE : "II" }

class Parameter:
    def __init__(self, name, format, required=False, value=None,
                 formatter=None):
        self.name = name
        self.format = format
        self.required = required
        self.formatter = formatter

        if value:
            self.set_value(value)
        else:
            self.value = ""

    def set_value(self, value):
        # Specialized Formatter Set
        if self.formatter:
            value = self.formatter(value)
            # This is a hack, must decided on ONE way to check
            # size and do formatting
            if self.formatter == fmt_st:
                self.format = "%ss" % len(value)

        # Default string formatter
        elif "s" in self.format:
            string_format = "%%-%s" % self.format
            value = string_format % value
        
        self.value = struct.pack(self.format, value)
        logger.debug('Set parameter %s to "%s"' % (self.name,
                                                   self.value))

class ResultValue:
    def __init__(self, name, format, offset=0):
        self.name = name
        self.format = format
        self.offset = offset

class Result:
    def __init__(self, name, result_values=[]):
        self.name = name
        self.result_values = result_values

    def handle(self, printer):
        pass


class DefaultResult(Result):
    status_1_return_codes = {
        128 : (OutofPaperError, 'Printer is out of paper'),
        64  : (AlmostOutofPaper, 'Printer almost out of paper'),
        32  : (PrinterError, 'Printer clock error'),
        16  : (PrinterError, 'Printer in error state'),
        8   : (CommandError, 'First data value in CMD is not ESC (1BH)'),
        4   : (CommandError, 'Nonexistent command'),
        2   : (CouponOpenError, 'Printer has a coupon currently open'),
        1   : (CommandError, 'Invalid number of parameters'),
        }

    status_2_return_codes = {
        128 : (CommandError, 'Invalid CMD parameter'),
        64  : (HardwareFailure, 'Fiscal memory is full'),
        32  : (HardwareFailure, 'Error in CMOS memory'),
        16  : (PrinterError, 'Given tax is not programmed on the printer'),
        8   : (DriverError, 'No available tax slot'),
        4   : (DriverError, 'Cancel operation is not allowed'),
        2   : (PrinterError, ('Owner data (CGC/IE) not programmed on the '
			      'printer')),
        1   : (CommandError, 'Command not executed'),
        }
    
    def __init__(self):
        Result.__init__(self, 'Default',
                        [ResultValue('ack', 'B', 0),
                         ResultValue('st1', 'B', 1),
                         ResultValue('st2', 'B', 2)])

    def update_format(self):
        self.format = "".join([p.format for p in self.result_values])
        self.data_size = struct.calcsize(self.format)
        logger.debug('Result format for %s: %s' % (self.name, self.format))

    def handle(self, printer):
        self.update_format()

        self.data = printer.read_insist(self.data_size)

        try:
            self.ack, self.st1, self.st2 = struct.unpack(self.format,
                                                         self.data)
        except:
            raise ValueError("Data received inconsistent with data expected")

        assert self.ack == 0x06
        self.describe_data()
        
    def describe_data(self):
        for key in self.status_1_return_codes.keys():
            if self.st1 & key:
                exception, message = self.status_1_return_codes[key]
                logger.debug('Status ST1:%s' % message)
                logger.warning(message)
                raise exception(message)

        if self.st1 == 0:
            logger.debug('Status ST1:Success, no error returned')

        for key in self.status_2_return_codes.keys():
            if self.st2 & key:
                exception, message = self.status_2_return_codes[key]
                logger.debug('Status ST2:%s' % message)
                logger.warning(message)
                raise exception(message)

        if self.st2 == 0:
            logger.debug('Status ST2:Success, no error returned')


class Command:
    """A Printer command.

    Has the capability to build command data streams.
    """
    
    # The MP-25FI Supports two protocols (this is the first one, also supported
    # by MP-20FI II)
    #
    # Graphical representation of a simple command (summarize, no parameters)
    #
    # 0x2|0x4|0x0|0x1b|0x6 |0x21|0x0
    #  |   |   |   |    |    |    |
    #  |   |   |   |    |    |    +--> CSH (most signifant byte of the sum of
    #  |   |   |   |    |    |          bytes in CMD_PROTO+CMD+CMPARAMETERS)
    #  |   |   |   |    |    +-------> CSL (least signifant byte of the sum
    #  |   |   |   |    |               of bytes in CMD_PROTO+CMD+CMPARAMETERS)
    #  |   |   |   |    +------------> CMD (summarize)
    #  |   |   |   |  
    #  |   |   |   +-----------------> CMD_PROTO (id for protocol one,presented
    #  |   |   |                       as part of CMD, here called CMD_PROTO)
    #  |   |   +---------------------> NBH (most significant byte of sum of 
    #  |   |                           bytes that will be sent to the printer)
    #  |   +-------------------------> NBL (least significant byte of sum of 
    #  |                               bytes that will be sent to the printer)
    #  +-----------------------------> STX (start of transmission)
    #
    # Note: CMD_PROTO is *not* in the manual, it's a made up name.
    #
    # Graphical representation of a slightly more complex command
    # (get_variables, with parameter)
    # 0x2|0x5|0x0|0x1b|0x23|0xd |0x4b|0x0
    #  |   |   |   |    |    |    |    |
    #  |   |   |   |    |    |    |    +--> CSH 
    #  |   |   |   |    |    |    +-------> CSL
    #  |   |   |   |    |    +------------> CMD_PARAM
    #  |   |   |   |    +-----------------> CMD 
    #  |   |   |   +----------------------> CMD_PROTO
    #  |   |   +--------------------------> NBH 
    #  |   +------------------------------> NBL 
    #  +----------------------------------> STX
    #
    # Note: CMD_PARAM is also *not* in the manual, it's made up name.

    STX_FMT = "B"
    NBL_FMT = "B"
    NBH_FMT = "B"
    CMD_PROTO_FMT = "B"
    CMD_FMT = "B"
    CMD_PARAM_FMT = ""
    CSL_FMT = "B"
    CSH_FMT = "B"

    # stx always is 0x2h
    STX = 0x02
    # CMD_PROTO is 0x1b for proto version 1
    #              0x1c for proto version 2 (support not implemented here)
    CMD_PROTO = 0x1b

    def __init__(self, cmd_code, cmd_name="", cmd_parameters=[], result=None, **kwargs):
        
        self.code = cmd_code
        self.name = cmd_name
        self.parameters = cmd_parameters

        self.update_command_format()

        if result == None:
            result = DefaultResult()
        
        self.result = result

        # Parameter Index, for easier lookup
        self.parameters_index = { }
        for p in self.parameters:
            self.parameters_index[p.name] = p

        # Set values
        for k, v in kwargs.items():
            if self.parameters_index.has_key(k):
                p = self.parameters_index[k]
                p.set_value(v)

    def check_required_parameters(self):
        for p in self.parameters:
            if p.required and not p.value:
                raise ValueError("Required parameter not set: %s" % p.name)

    def has_result(self):
        if self.result:
            return True
        else:
            return False

    def set_parameter_value(self, parameter_name, value):
        p = self.parameter_index[parameter_name]
        p.set_value(value)

    def update_command_format(self):
        self.command_format = self.STX_FMT + \
                              self.NBL_FMT + \
                              self.NBH_FMT + \
                              self.CMD_PROTO_FMT + \
                              self.CMD_FMT + \
                              "".join([p.format for p in self.parameters \
                                       if (p.value or p.required)]) + \
                              self.CSL_FMT + \
                              self.CSH_FMT

    def get_command_format(self):
        self.update_command_format()
        return self.command_format

    def update_command(self):
        """Updates self.command with a command build from the selected
        parameters"""
        
        self.update_command_format()
     
        self.nbl = self.calculate_nbl()
        self.nbh = self.calculate_nbh()
        self.csl = self.calculate_csl()
        self.csh = self.calculate_csh()

        # Unfortunately we cannot use *args for the parameter data, and then
        # supply the other arguments to pack (self.csl, self.csh). Or am I
        # missing something?
        fmt_up_to_cmd = self.command_format[:5]
        data_up_to_cmd = struct.pack(fmt_up_to_cmd,
                                     self.STX,
                                     self.nbl,
                                     self.nbh,
                                     self.CMD_PROTO,
                                     self.code)

        fmt_parameter = self.command_format[5:-2]
        data_parameter = struct.pack(fmt_parameter,
                                     *[p.value for p in self.parameters\
                                       if (p.value or p.required)])

        fmt_trailer = self.command_format[-2:]
        data_trailer = struct.pack(fmt_trailer,
                                   self.csl,
                                   self.csh)

        self.command = data_up_to_cmd + data_parameter + data_trailer

        logger.debug("command %s %s" % (self.name, 
              "|".join([hex(ord(i)) for i in self.command])))

    def get_command(self):
        self.update_command()
        return self.command
        
    def command_parameters_trailler_length(self):
        """Returns the size of part of one command data stream, as shown
        by the illustration bellow:

        |STX|NBL|NBH|CMD|CSL|CSH|
                     ^^^^^^^^^^^^

        If parameters is passed, it's expected to be a string and produce
        a correct result when used with a len(). If it's not passed, its
        size is calculated from the self.parameters list.
        """

        len_parameters = len("".join([p.value for p in self.parameters if \
                                      p.value]))
        length = struct.calcsize(self.CMD_PROTO_FMT) + \
                 struct.calcsize(self.CMD_FMT) + \
                 len_parameters + \
                 struct.calcsize(self.CSL_FMT) + \
                 struct.calcsize(self.CSH_FMT)
        return length

    def calculate_nbl(self):
        """Returns least significant byte of the total length of CMD,
        CSL and CSH"""

        length = self.command_parameters_trailler_length()
        return length & 0x00FF
        
    def calculate_nbh(self):
        """Returns most significant byte of the total length of CMD,
       CSL and CSH"""
        length = self.command_parameters_trailler_length()
        return length & 0xFF00

    def checksum_of_command_parameter(self):
        """Returns the sum of individual bytes of one command data stream,
        as shown by the illustration bellow:

        |STX|NBL|NBH|CMD|CSL|CSH|
                     ^^^
        """
        data = struct.pack(self.CMD_PROTO_FMT + self.CMD_FMT,
                           self.CMD_PROTO, self.code) + \
                           "".join([p.value for p in self.parameters if\
                                    p.value])
        total = 0
        for byte in map(ord, data):
            total = total + byte
        return total
    
    def calculate_csl(self):
        """Returns least significant byte of the sum of bytes in CMD"""
        checksum = self.checksum_of_command_parameter()
        return checksum & 0x00FF

    def calculate_csh(self):
        """Returns most significant byte of the sum of bytes in CMD"""
        checksum = self.checksum_of_command_parameter()
        return (checksum & 0xFF00) >> 8

    def print_info(self):
        print 'Command:', self.name
        print ' code =', self.code
        print ' parameters:'
        for p in self.parameters:
            print '  ', p.name, p.format, p.value, p.required
        print ' data_full_stream', \
              self.pretty_print_data_stream(self.update_command())

    def pretty_format_data_stream(self, data_stream):
        return "|".join([hex(ord(i)) for i in data_stream])

    def pretty_print_data_stream(self, data_stream):
        print self.pretty_format_data_stream(data_stream)


# These are printer commands, represented as classes
# To use then, instantiate it, and send them to send_command() method

class SummarizeCommand(Command):
    def __init__(self, **kwargs):
        Command.__init__(self, 6, "Summarize",
                         **kwargs)

class CloseTillCommand(Command):
    def __init__(self, **kwargs):
        Command.__init__(self, 5, "CloseTillCommand",
                         [Parameter('datetime', '13s')],
                         **kwargs)

class GetStatusCommand(Command):
    def __init__(self, **kwargs):
        Command.__init__(self, 19, "GetStatus",
                         **kwargs)

class CouponOpenCommand(Command):
    # Bematech seems have a off-by-one bug in these fields
    # The documentation says CPF should be 28 chars long,
    # but this breaks the other two fields. setting it to
    # 29 char seems to fix this issue
    def __init__(self, **kwargs):
        Command.__init__(self, 0, "CouponOpen",
                         [Parameter("cpf", "29s"),
                          Parameter("name", "30s"),
                          Parameter("address", "80s")],
                         **kwargs)

class CouponCancelCommand(Command):
    def __init__(self, **kwargs):
        Command.__init__(self, 14, "CouponCancel",
                         [Parameter("cpf", "28s"),
                          Parameter("name", "30s"),
                          Parameter("address", "80s")],
                         **kwargs)


class CouponAddItemCommand(Command):
    def __init__(self, **kwargs):
        Command.__init__(self, 56, "CouponAddItem",
                         [Parameter("code", "13s", True),
                          Parameter("description", "29s", True),
                          Parameter("taxcode", "2s", True, "II"),
                          Parameter("quantity", "7s", True,
                                    formatter=fmt_fl_7c_3d_nodot),
                          Parameter("price", "8s", True,
                                    formatter=fmt_fl_8c_3d_nodot),
                          Parameter("discount", "4s", True, "0000")],
                         **kwargs)

class CouponAddItemWithUnitCommand(Command):
    def __init__(self, **kwargs):
        Command.__init__(self, 63, "CouponAddItemWithUnit",
                         [Parameter("tax", "2s", True, "II"),
                          Parameter("price", "9s", True),
                          Parameter("quantity", "7s", True),
                          Parameter("discount_by_value", "10s", True,
                                    "0000000000"),
                          Parameter("extra_charge_by_percentage", "10s", True,
                                    "0000000000"),
                          Parameter("padding_not_used", "22s", True,
                                    "0000000000000000000000"),
                          Parameter("unit", "2s", True),
                          Parameter("code", "49s", True),
                          Parameter("description", "201s", True)],
                         **kwargs)

class StartClosingCouponCommand(Command):
    def __init__(self, **kwargs):
        Command.__init__(self, 32, "StartClosingCoupon",
                         [Parameter("charge_type", "1s", True),
                          Parameter("charge_value", "4s", True)],
                         **kwargs)

class DiscountCouponCommand(Command):
    def __init__(self, **kwargs):
        Command.__init__(self, 104, "DiscountCoupon",
                         [Parameter("op_type", "1s", True),
                          # Either percentage or value is required
                          Parameter("percentage", "4s"),
                          Parameter("value", "14s")],
                         **kwargs)

class TotalizeCouponCommand(Command):
    def __init__(self):
        Command.__init__(self, 106, "TotalizeCoupon")

class CouponAddPayment(Command):
    def __init__(self, **kwargs):
        Command.__init__(self, 72, "CouponAddPayment",
                         [Parameter("method", "2s", True),
                          Parameter("value", "14s", True,
                                    formatter=fmt_fl_14c_2d_nodot),
                          Parameter("description", "80s")],
                         **kwargs)

class CouponCloseCommand(Command):
    def __init__(self, **kwargs):
        Command.__init__(self, 34, "CouponClose",
                         [Parameter("message", "492s", False,
                                    formatter=fmt_st)],
                         **kwargs)

class CancelItemCommand(Command):
    def __init__(self, **kwargs):
        Command.__init__(self, 31, "CancelItem",
                         [Parameter('item_number', '4s', True)],
                         **kwargs)

class GetSubTotalCommand(Command):
    def __init__(self):
        Command.__init__(self, 29, "GetSubTotalCommand")


payment_methods = {
    MONEY_PM : "01",
    CHEQUE_PM : "02"
}


class MP25Printer(SerialBase):

    implements(ICouponPrinter)

    printer_name = "Bematech MP25 FI"

    def __init__(self, *args, **kwargs):
        SerialBase.__init__(self, *args, **kwargs)
        self.remainder_value = 0.00

    def _check(self):
        """Check the printer status after sending a commit"""
        pass

    def _send_command(self, command):
        self.setTimeout(5)
        self.setWriteTimeout(5)
        self.write(command.get_command())
        command.result.handle(self)

    #
    # Helper methods
    #

    def get_coupon_subtotal(self):
        self.write(GetSubTotalCommand().get_command())

        # Return value: 3 Bytes (Status) + 7 Bytes (Subtotal in BCD format)
        # Man page #49
        data = self.read_insist(10)
        try:
            ack, st1, st2, subtotal = struct.unpack("BBB7s", data)
        except:
            raise ValueError("Data received inconsistent with data expected")
        
        return float(''.join(['%x' % ord(i) for i in subtotal])) / 1e4

    #
    # This implements the ICouponPrinter Interface
    #

    def summarize(self):
        """
        Prints a summary of all sales of the day
        """
        self._send_command(SummarizeCommand())

    def close_till(self):
        """
        Close the till for the day, no other actions can be done
        after this is called
        """
        raise NotImplementedError, 'DO NOT USE THIS FOR NOW'
        self._send_command(CloseTillCommand())

    def get_status(self):
        """
        Returns a 3 sized tuple of boolean: Offline, OutOfPaper, Failure
        """
        self._send_command(GetStatusCommand())

    def coupon_open(self, company, address, document):
        """
        This needs to be called before anything else
        """

        if company or address or document:
            self._send_command(CouponOpenCommand(cpf=document,
                                                 name=company,
                                                 address=address))
        else:
            self._send_command(CouponOpenCommand())
        self.item_counter = 0

    def coupon_cancel(self):
        """
        Can only be called when a coupon is opened.
        It needs to be possible to open new coupons after this is called.
        """
        self._send_command(CouponCancelCommand())

    def coupon_close(self, message=""):
        """
        This can only be called when the coupon is open,
        has items added, payments added and totalized is called
        It needs to be possible to open new coupons after this is called.
        """
        self._send_command(CouponCloseCommand(message=message))
        self.item_counter = 0

    def coupon_add_item(self, code, quantity, price, unit,
                        description, taxcode, discount, markup):

        if discount or markup or unit:
            # Use command #63, not done yet
            pass

        taxcode = tax_translate_dict[taxcode]

        self._send_command(CouponAddItemCommand(code=code,
                                               quantity=quantity,
                                               price=price,
                                               description=description,
                                               taxcode=taxcode))
        self.item_counter += 1
        return self.item_counter

    def coupon_cancel_item(self, item_id=None):
        """ Cancel an item added to coupon; if no item id is specified, 
        cancel the last item added. """
        # We would can use an apropriate command to cancel the last 
        # item added (command #13, man page 34),  but as we already
        # have an internal counter, I don't think that this is necessary.
        if not item_id:
            item_id = self.item_counter
        self._send_command(CancelItemCommand(item_number='%04d' % item_id))

    def coupon_add_payment(self, payment_method, value, description=''):
        pm = payment_methods[payment_method]
        self._send_command(CouponAddPayment(method=pm, value=value,
                                            description=description))
        self.remainder_value -= value
        if self.remainder_value < 0.0:
            self.remainder_value = 0.0
        return self.remainder_value

    def coupon_totalize(self, discount, markup, taxcode):
        if discount:
            type = 'D'
            val = '%04d' % discount
        elif markup:
            type = 'A'
            val = '%04d' % markup
        else:
            type = 'A'
            # Just to use the StartClosingCoupon in case of no discount/markup
            # be specified.
            val = '%04d' % 0

        self ._send_command(StartClosingCouponCommand(charge_type=type,
                                                      charge_value=val))
        totalized_value = self.get_coupon_subtotal()
        self.remainder_value = totalized_value
        return totalized_value
        

    #
    # Here ends the implementation of the ICouponPrinter Driver Interface
    #

