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
Daruma FS2100 driver
"""

import operator
from decimal import Decimal

from stoqdrivers.devices.printers.daruma.FS345 import FS345
from stoqdrivers.constants import UNIT_CUSTOM, UNIT_EMPTY

CMD_ADD_ITEM = 201

class FS2100(FS345):
    model_name = "Daruma FS 2100"

    def coupon_add_item(self, code, description, price, taxcode,
                        quantity=Decimal("1.0"), unit=UNIT_EMPTY,
                        discount=Decimal("0.0"),
                        surcharge=Decimal("0.0"), unit_desc=""):
        taxcode = self._consts.get_value(taxcode)
        if surcharge:
            d = 2
            E = surcharge
        else:
            d = 0
            E = discount

        # The minimum size of the description, when working with one line for
        # description; if 0, write in multiple lines, if necessary.
        desc_size = 0

        if unit != UNIT_CUSTOM:
            unit = self._consts.get_value(unit)
        else:
            unit = unit_desc
        # XXX: We need test correctly if the price's calcule is right (we
        # don't can do it right now since the manual isn't so clean).
        data = ('%2s'  # Tributary situation
                '%07d' # Quantity
                '%08d' # Unitary price
                '%d'   # 0=Discount(%) 1=Discount($) 2=Surcharge(%) 3=Surcharge($)
                '%03d' # Discount/Surcharge value
                '%07d' # *Padding* (since we have discount/surcharge only in %)
                '%02d' # Description size
                '%14s' # Code
                '%3s'  # Unit of measure
                '%s'   # Product description
                '\xff' # EOF
                % (taxcode, int(quantity), int(price * 1e3), d, int(E * 1e3),
                   0, desc_size, code, unit, description[:233]))

        value = self.send_new_command(CMD_ADD_ITEM, data)
        return int(value[3:6])

    def send_new_command(self, command, extra=''):
        """ This method is used to send especific commands to model FS2100.
        Note that the main differences are the prefix (0x1c + 'F', since we
        will use a function of the FS2100 superset) and the checksum, that
        must be included in the end of all the functions of this superset.
        """
        data = chr(command) + extra

        self.debug('N>>> %r %d' % (data, len(data)))
        data = '\x1cF' + data

        checksum = reduce(operator.xor, [ord(d) for d in data], 0)
        self.write(data + chr(checksum))

        retval = self.readline()
        if retval.startswith(':E'):
            self.handle_error(retval, data)

        return retval[1:]

