# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## Author(s):   Ronaldo Maia <romaia@async.com.br>
##
"""
Bematech MP20 driver

The MP20 is compatible with the MP25 command set (actually its the other way
around ;) until a certain command (85, I think). Commands above that are just
not executed.

There are some differences on the Registers numbering as well.

Also, some commands have different parameter sizes. These are:

CMD             MP 20                MP 25
00              29                  28+30+80 (abertura de cupom)
14              -                   28+30+80 (cancelamento de cupom)
32                                           (inicia fechamento cupom)
73              Algumas diferencas no funcionamento. Ver manual.
"""

from kiwi.log import Logger
from decimal import Decimal

from stoqdrivers.printers.bematech.MP25 import (MP25, MP25Status, CMD_STATUS,
                                                CMD_COUPON_OPEN)

log = Logger('stoqdrivers.bematech.MP20')

CMD_ADD_ITEM_SIMPLE = 9


class MP20Registers(object):
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
    SERIAL = 0
    FIRMWARE = 1

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
        SERIAL: ('15s', False),
        FIRMWARE: ('3s', True),
    }


class MP20Status(MP25Status):
    def __init__(self, reply):
        self.st1, self.st2 = reply[-2:]
        self.st3 = 0


class MP20(MP25):
    model_name = "Bematech MP20 TH FI"
    CMD_PROTO = 0x1b

    registers = MP20Registers
    supports_duplicate_receipt = False
    reply_format = '<b%sbb'
    status_size = 2

    #
    #   MP25 implementation
    #

    def coupon_open(self):
        """ This needs to be called before anything else. """
        self._send_command(CMD_COUPON_OPEN,
                           "%-29s" % (self._customer_document))

    def coupon_add_item(self, code, description, price, taxcode,
                        quantity=Decimal("1.0"), unit=None,
                        discount=Decimal("0.0"), markup=Decimal("0.0"),
                        unit_desc=""):

        # We are using a simpler command for adding items with the MP20
        # because its not working with the MP25 command (ESC 63). This
        # simpler command does not support markup and unit
        data = (
                "%-13s"  # code
                "%29s" # description
                "%02s"     # taxcode
                "%07d"     # quantity
                "%08d"     # value
                "%08d"    # discount
                % (code, description, taxcode,
                   quantity * Decimal("1e3"),
                   price * Decimal("1e2"),
                   discount * Decimal("1e2")))

        self._send_command(CMD_ADD_ITEM_SIMPLE, data)
        return self._get_last_item_id()

    def get_status(self, val=None):
        if val is None:
            val = self._send_command(CMD_STATUS, raw=True)

        return MP20Status(val)

    def cancel_last_coupon(self):
        """Cancel the last non fiscal coupon or the last sale."""
        #XXX MP20 does not support this
        self.coupon_cancel()

    def get_ccf(self):
        # MP20 does not support this. We should just return the coo
        # http://www.forumweb.com.br/foruns/lofiversion/index.php/t64417.html
        return self.get_coo()

    def status_reply_complete(self, reply):
        log.debug('status_reply_complete "%s" (size=%s)' % (reply, len(reply)))
        return len(reply) == 18


