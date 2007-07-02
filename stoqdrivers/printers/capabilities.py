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
Driver Capability management.
"""

from kiwi.argcheck import argcheck, number

from stoqdrivers.exceptions import CapabilityError

class capcheck(argcheck):
    """ A extension for argcheck that validates a value with base in the driver
    capabilities.  Note that the instance where this class is used as decorator
    must have defined a get_capabilities  method that returns a dictionary with
    the driver capabilities.
    """

    def extra_check(self, arg_names, types, cargs, kwargs):
        keyvalues = zip(arg_names, cargs[1:])
        kwargs = kwargs.copy()
        kwargs.update(dict(keyvalues))
        self._check_capabilities(cargs[0], **kwargs)

    def _check_capabilities(self, inst, **kwargs):
        caps = inst.get_capabilities()

        for key, value in kwargs.items():
            capability = caps.get(key)
            if not capability:
                continue
            try:
                capability.check_value(value)
            except CapabilityError, e:
                raise CapabilityError("invalid value for '%s': %s" % (key, e))


class Capability:
    """ This class is used to represent a driver capability, offering methods
    to validate a value with base in the capability limits.
    """

    @argcheck(int, int, number, number, int, number)
    def __init__(self, min_len=None, max_len=None, max_size=None,
                 min_size=None, digits=None, decimals=None):
        """ Creates a new driver capability.  A driver capability can be
        represented basically by the max length of a string, the max digits
        number of a value or its minimum/maximum size.  With an instance of
        Capability you can check if a value is acceptable by the driver
        through the check_value method.  The Capability arguments are:

        @param min_len:    The minimum length of a string
        @type min_len:     number
        @param max_len:    The max length of a string
        @type max_len:     number
        @param max_size    The maximum size for a value
        @type max_size:    number
        @param min_size:   The minimum size for a value
        @type min_size:    number
        @param digits:     The number of digits that a number can have
        @type digits:      number
        @param decimals:   If the max value for the capability is a float,
                           this parameter specifies the max precision
                           that the number can have.
        @type decimals:    number

        Note that 'max_len' can't be used together with 'min_size', 'max_size'
        and 'digits', in the same way that 'max_size' and 'min_size' can't be
        used with 'digits'.  The values defined for these parameters are used
        also to verify the value type in the 'check_value' method.
        """

        if max_len is not None and (max_size is not None
                                    and min_size is not None
                                    and digits is not None
                                    and decimals):
            raise ValueError("max_len cannot be used together with max_size, "
                             "min_size, digits or decimals")
        if digits is not None:
            if max_size is not None:
                raise ValueError("digits can't be used with max_size")
            if decimals:
                decimal_part = 1 - (1 / 10.0 ** decimals)
            else:
                decimal_part = 0
            self.max_size = ((10.0 ** digits) - 1) + decimal_part

        self.min_len = min_len
        self.max_len = max_len
        self.min_size = min_size or 0
        self.max_size = max_size
        self.digits = digits
        self.decimals = decimals

    def check_value(self, value):
        if self.max_len:
            if not isinstance(value, basestring):
                raise CapabilityError("the value must be a string")
            if len(value) > self.max_len:
                raise CapabilityError("the value can't be greater than %d "
                                      "characters" % self.max_len)
            elif len(value) < self.min_len:
                raise CapabilityError("the value can't be less than %d "
                                      "characters" % self.min_len)
            return
        elif not (self.max_size and self.min_size):
            return

        if not isinstance(value, (float, int, long)):
            raise CapabilityError("the value must be float, integer or long")

        if value > self.max_size:
            raise CapabilityError("the value can't be greater than %r"
                                  % self.max_size)
        elif value < self.min_size:
            raise CapabilityError("the value can't be less than %r"
                                  % self.min_size)

