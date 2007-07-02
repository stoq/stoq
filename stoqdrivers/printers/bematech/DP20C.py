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
## Author(s):   Henrique Romano <henrique@async.com.br>
##
"""
Bematech DP20C driver
"""

import datetime

from zope.interface import implements

from stoqdrivers.interfaces import IChequePrinter
from stoqdrivers.printers.cheque import BaseChequePrinter
from stoqdrivers.printers.capabilities import Capability
from stoqdrivers.serialbase import SerialBase

class DP20C(SerialBase, BaseChequePrinter):
    CMD_PREFIX = '\x1B'
    CMD_SUFFIX = '\x0D'
    CMD_SETUP_COORDINATES = '\xAA'

    implements(IChequePrinter)

    model_name = "Bematech DP20C"
    cheque_printer_charset = "cp850"

    def __init__(self, port, consts=None):
        SerialBase.__init__(self, port)
        BaseChequePrinter.__init__(self)

    def _setup_positions(self, bank):
        # man page 24.
        data = [(bank.get_x_coordinate("value") - 60) / 10,
                (bank.get_x_coordinate("value") - 60) % 10,
                bank.get_y_coordinate("value"),
                bank.get_x_coordinate("legal_amount") / 10,
                bank.get_x_coordinate("legal_amount") % 10,
                bank.get_y_coordinate("legal_amount"),
                bank.get_x_coordinate("legal_amount2") % 10,
                bank.get_y_coordinate("legal_amount2") % 10,
                bank.get_x_coordinate("thirdparty") % 10,
                bank.get_y_coordinate("thirdparty") % 10,
                bank.get_x_coordinate("city") / 10,
                bank.get_x_coordinate("day") / 10,
                bank.get_x_coordinate("day") % 10,
                bank.get_x_coordinate("month") / 10,
                bank.get_x_coordinate("month") % 10,
                bank.get_x_coordinate("year") % 10]
        data = "".join([str(d) for d in data])
        self.write("%c%c987? %s%c" % (DP20C.CMD_PREFIX,
                                      DP20C.CMD_SETUP_COORDINATES,
                                      data, DP20C.CMD_SUFFIX))

    def _setup_cheque(self, bank, value, thirdparty, city,
                      date=None):
        if date is None:
            date = datetime.datetime.now()
        self._setup_positions(bank)
        value = "%.02f" % value
        if "." in value:
            value.replace(".", ",")
        date = date.strftime("%02d/%02m/%Y")
        bank_code = "987"
        for idx, data in enumerate((thirdparty, city, bank_code, value, date)):
            s = "%c%s" % (0xA0 + idx, data)
            self.write(DP20C.CMD_PREFIX + s + DP20C.CMD_SUFFIX)

    def _print_cheque(self):
        for data in (0xB1, 0xB0):
            self.write(DP20C.CMD_PREFIX + chr(data))

    #
    # IChequePrinter implementation
    #

    def print_cheque(self, *args, **kwargs):
        self._setup_cheque(*args, **kwargs)
        self._print_cheque()

    def get_capabilities(self):
        # XXX: The Bematech DP20C manual doesn't specify what are the
        # parameter max values, so...
        return {'cheque_thirdparty': Capability(),
                'cheque_value': Capability(),
                'cheque_city': Capability()}
