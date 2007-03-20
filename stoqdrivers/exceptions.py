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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
StoqDrivers exceptions definition
"""

class CriticalError(Exception):
    "Unknown device type or bad config settings"

class ConfigError(Exception):
    "Bad config file arguments or sections"

class CommError(Exception):
    "Common communication failures"

class PrinterError(Exception):
    "General printer errors"

class DriverError(Exception):
    "Base exception for all printer errors"
    def __init__(self, error='', code=-1):
        if code != -1:
            error = '%d: %s' % (code, error)
        Exception.__init__(self, error)
        self.code = code

class OutofPaperError(DriverError):
    "No paper left"

class PrinterOfflineError(DriverError):
    "Printer is offline"

class AlmostOutofPaper(DriverError):
    "Almost out of paper"

class HardwareFailure(DriverError):
    "Unknown hardware failure"

class PendingReduceZ(DriverError):
    "A Reduce Z is pending"

class PendingReadX(DriverError):
    "A Read X is pending"

class CloseCouponError(DriverError):
    "Could not close the coupon."

class CouponNotOpenError(DriverError):
    "Coupon is not open."

class CouponOpenError(DriverError):
    "Coupon already is open."

class AuthenticationFailure(DriverError):
    "General authentication failure"

class CommandParametersError(DriverError):
    "Parameters sent to printer are wrong."

class CommandError(DriverError):
    "Command sent to printer is wrong."

class ClosedTillError(DriverError):
    "No transactions can be done while the till is closed."

class ReduceZError(DriverError):
    "A Reduce already done."

class ReadXError(DriverError):
    "A Read X is already done."

class CouponTotalizeError(DriverError):
    "Error while totalizing a coupon."

class PaymentAdditionError(DriverError):
    "Error while adding a payment."

class CancelItemError(DriverError):
    "Error while cancelling coupon item."

class InvalidState(DriverError):
    "Invalid state for the requested operation."

class CapabilityError(Exception):
    "General capability error."

class ItemAdditionError(DriverError):
    "Error while adding an item."

class InvalidReply(DriverError):
    "Invalid reply received"

class AlreadyTotalized(DriverError):
    "The coupon is already totalized"

class InvalidValue(DriverError):
    "The value specified is invalid or is not in the expected range"
