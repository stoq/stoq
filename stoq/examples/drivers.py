#!/usr/bin/env python
# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
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
## Author(s): Henrique Romano <henrique@async.com.br>
##
"""
stoq/examples/drivers.py:

    Create a PrinterSetting object that use a VirtualPrinter by default.
"""

import socket

from stoq.lib.runtime import new_transaction, print_msg
from stoq.domain.drivers import PrinterSettings

def create_printer_setting():
    print_msg("Creating default printer settings...", break_line=False)
    conn = new_transaction()
    printer = PrinterSettings(connection=conn)
    printer.host = socket.gethostname()
    printer.device = PrinterSettings.DEVICE_SERIAL1
    printer.brand = 'virtual'
    printer.model = 'Simple'
    conn.commit()
    print_msg("done.")

if __name__ == "__main__":
    create_printer_setting()
