# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Fiscal Printer
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoqdrivers/drivers/skeleton.py:
    
    A skeleton for all Fiscal Printer drivers.
"""

from stoqdrivers.drivers.interface import IFiscalPrinterDriver


class Driver:
    """A general definition for a driver"""

    __implements__ = IFiscalPrinterDriver

    def __init__(self, config):
        pass



    #
    # Initializing Fiscal Printer
    #



    def setup_printer(self):
        """Some important mandatory tasks before start using the printer
        like:
            - Set sale parameters
            - Set taxes table
            - Set information for non-fiscal operations
            - Set payment method informations
            - Set printer clock
            - Set printer user information
        """


    #
    # I/O API
    #



    def _write(self, command):
        """Send a command to a fiscal printer"""

    def _check(self):
        """Check the printer status after sending a commit"""



    #
    # Formatting data
    #



    # Evaluate a good API for this section



    #
    # Fiscal Printer API - Implementation of IFiscalPrinterDriver methods
    #

