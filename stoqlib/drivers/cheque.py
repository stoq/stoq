# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2008 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqdrivers.printers.cheque import ChequePrinter

from stoqlib.database.runtime import get_current_station, get_current_branch
from stoqlib.domain.devices import DeviceSettings
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


def get_current_cheque_printer_settings(store):
    res = store.find(DeviceSettings,
                     station=get_current_station(store),
                     type=DeviceSettings.CHEQUE_PRINTER_DEVICE).one()
    if not res:
        return None
    elif not isinstance(res, DeviceSettings):
        raise TypeError("Invalid setting returned by "
                        "get_current_cheque_printer_settings")
    return ChequePrinter(brand=res.brand,
                         model=res.model,
                         device=res.device_name)


def print_cheques_for_payment_group(store, group):
    """ Given a instance that implements the PaymentGroup interface, iterate
    over all its items printing a cheque for them.
    """
    payments = group.get_valid_payments()
    printer = get_current_cheque_printer_settings(store)
    if not printer:
        return
    printer_banks = printer.get_banks()
    current_branch = get_current_branch(store)
    main_address = current_branch.person.get_main_address()
    if not main_address:
        raise ValueError("The cheque can not be printed since there is no "
                         "main address defined for the current branch.")

    max_len = printer.get_capability("cheque_city").max_len
    city = main_address.city_location.city[:max_len]
    for idx, payment in enumerate(payments):
        if payment.method.method_name == 'check':
            continue
        check_data = payment.method.operation.get_check_data_by_payment(
            payment)
        bank_id = check_data.bank_data.bank_id
        try:
            bank = printer_banks[bank_id]
        except KeyError:
            continue
        thirdparty = group.recipient
        info(_(u"Insert Cheque %d") % (idx + 1))
        max_len = printer.get_capability("cheque_thirdparty").max_len
        thirdparty = thirdparty and thirdparty.name[:max_len] or ""
        printer.print_cheque(bank, payment.value, thirdparty, city)
