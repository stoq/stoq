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
## Author(s):   Johan Dahlin     <jdahlin@async.com.br>
##

from kiwi.argcheck import argcheck, number, percent

from fiscalprinter.exceptions import CriticalError
from fiscalprinter.exceptions import CloseCouponError, PaymentAdditionError
from fiscalprinter.exceptions import (PendingReadX, PendingReduceZ,
                                      CouponOpenError)
from fiscalprinter.configparser import FiscalPrinterConfig
from fiscalprinter.constants import (TAX_NONE,TAX_IOF, TAX_ICMS,
                                     TAX_SUBSTITUTION, TAX_EXEMPTION)
from fiscalprinter.constants import (UNIT_EMPTY, UNIT_LITERS,
                                     UNIT_WEIGHT, UNIT_METERS)
from fiscalprinter.constants import MONEY_PM, CHEQUE_PM
from fiscalprinter.log import Logger

#
# Extra data types to argcheck
#

class taxcode(number):
    @classmethod
    def value_check(cls, name, value):
        if value not in (TAX_NONE, TAX_IOF, TAX_ICMS, TAX_SUBSTITUTION,
                         TAX_EXEMPTION):
            raise ValueError("%s must be one of TAX_* constants" % name)

class unit(number):
    @classmethod
    def value_check(cls, name, value):
        if value not in (UNIT_WEIGHT, UNIT_METERS, UNIT_LITERS,
                         UNIT_EMPTY):
            raise ValueError("%s must be one of UNIT_* constants" % name)

class payment_method(number):
    @classmethod
    def value_check(cls, name, value):
        if value not in (MONEY_PM, CHEQUE_PM):
            raise ValueError("%s must be one of *_PM constants" % name)

#
# FiscalPrinter interface
#

class FiscalPrinter(Logger):
    log_domain = 'fp'
    def __init__(self, config_file=None):
        """On printer __init__ time, BaseDriver.__init__ gets called. This
        has the affect of setting up a self.device.

        The following device backends exist:
        - serial: uses pySerial
        - network: implemented in NetworkSerialDevice.py 
                    (usable with ser2net or something like it, 
                     not stable though...)

        To choose which device to use, add a key named 'device-type' to 
        the config dictionary that is passed to this constructor. Set its 
        value to either one of the backend names.

        The methods which actually transmit and receive data 
        (through a 'self.device') are:
                                        - self._write
                                        - self._read
        """
        Logger.__init__(self)
        
        self._load_configuration(config_file)
        self.has_been_totalized = False

    def _load_configuration(self, config_file):
        config = FiscalPrinterConfig(config_file)

        # Log printer/driver configuration 
        c = []
        device_type = config.get_devicetype()
        brand = config.get_brand()
        model = config.get_model()
        c.append(('model', model))
        c.append(('brand', brand))
        c.append(('devicetype', device_type))
        c.append(('device', config.get_device()))
        c.append(('baudrate', config.get_baudrate()))
        c.append(('port', config.get_port()))
        c.append(('host', config.get_host()))
        self.debug('Config data: %s\n' % ','.join(['='.join(i) for i in c]))

        name = 'fiscalprinter.drivers.%s.%s' % (brand, model)
        try:
            module = __import__(name, None, None, 'fiscalprinter')
        except ImportError, reason:
            raise CriticalError("Could not load driver %s: %s"
                                % (model, reason))

        class_name = model + 'Printer'

        driver_class = getattr(module, class_name, None)
        if driver_class is None:
            raise CriticalError("Printer driver %s needs a class "
                                "called %s" % (name, class_name))

        # Default is SerialDevice (pySerial)
        if device_type == 'serial':
            self._driver = driver_class(device=config.get_device(),
                                        baudrate=config.get_baudrate())
        # If the user is really nuts, he can try the NetworkSerialDevice
        #elif device_type == 'network':
        #    self._driver = NetworkSerialDevice(host=config.get_host(),
        #                                       port=config.get_port())
        else:
            raise CriticalError("Unknown 'device-type': check your "
                                "configuration file or supplied "
                                "'config' parameter and supply a "
                                "'device-type' of either 'serial', "
                                "'posixserial' or 'network'")

    @argcheck(str, str, str)
    def open(self, customer, address, document):
        self.info('coupon_open')
        return self._driver.coupon_open(customer, address, document)

    @argcheck(str, number, number, unit, str, taxcode, percent, percent)
    def add_item(self, code, quantity, price, unit, description,
                 taxcode, discount, charge):
        if discount and charge:
            raise TypeError("discount and charge can not be used together")

        self.info('coupon_add_item')
        return self._driver.coupon_add_item(code, quantity, price,
                                            unit, description,
                                            taxcode, discount, charge)
    @argcheck(percent, percent, taxcode)
    def totalize(self, discount, charge, taxcode):
        if discount and charge:
            raise TypeError("discount and charge can not be used together")

        self.info('coupon_totalize')
        result = self._driver.coupon_totalize(discount, charge, taxcode)
        self.has_been_totalized = True
        return result

    @argcheck(payment_method, float, str)
    def add_payment(self, payment_method, value, description=''):
        self.info('coupon_add_payment')
        if not self.has_been_totalized:
            raise PaymentAdditionError("You must totalize the coupon "
                                       "before add payments.")
        result = self._driver.coupon_add_payment(payment_method, value,
                                                 description)
        return result
        
    def cancel(self):
        self.info('coupon_cancel')
        return self._driver.coupon_cancel()

    def cancel_item(self, item_id):
        self.info('coupon_cancel_item')
        return self._driver.coupon_cancel_item(item_id)

    @argcheck(str)
    def close(self, message=''):
        self.info('coupon_close')
        if not self.has_been_totalized:
            raise CloseCouponError("You must totalize the coupon before close "
                                   "it.")
        return self._driver.coupon_close(message)

    def summarize(self):
        self.info('summarize')
        return self._driver.summarize()

    def close_till(self):
        self.info('close_till')
        return self._driver.close_till()

    def get_status(self):
        self.info('get_status')
        return self._driver.get_status()

def test():
    p = FiscalPrinter()

    while True:
        try:
            p.open('Zee germans', 'Home', 'yaya')
            break
        except CouponOpenError:
            p.cancel()
        except PendingReadX:
            p.summarize()
            return
        except PendingReduceZ:
            p.close_till()
            return

    i1 = p.add_item("foo", 1, 10.00, UNIT_EMPTY, "description", TAX_NONE, 0, 0)
    i2 = p.add_item("HK001", 5, 1.53, UNIT_LITERS, "Bohemia Beer", TAX_NONE,
                    0, 0)
    p.cancel_item(i1)

    coupon_total = p.totalize(0.0, 0, TAX_NONE)

    p.add_payment(MONEY_PM, 5.00, '')
    p.add_payment(MONEY_PM, 2.00, '')
    p.add_payment(MONEY_PM, 1.00, '')

    p.close()

if __name__ == '__main__':
    test()
