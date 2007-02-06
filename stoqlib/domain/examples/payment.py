# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):        Evandro Vale Miquelito     <evandro@async.com.br>
##
"""Create simple payments to an example database"""

from stoqlib.database.runtime import new_transaction
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.domain.examples import log
from stoqlib.domain.interfaces import ICreditProvider
from stoqlib.domain.person import Person
from stoqlib.domain.payment.methods import (CardInstallmentSettings,
                                            DebitCardDetails,
                                            CreditCardDetails,
                                            CardInstallmentsStoreDetails,
                                            CardInstallmentsProviderDetails,
                                            FinanceDetails)

_ = stoqlib_gettext



#
# Main
#



DEFAULT_CLOSING_DAY = 12
DEFAULT_PAYMENT_DAY = 15
DEFAULT_C0MMISION = 8

DEFAULT_RECEIVE_DAY = 5

MAX_INSTALLMENTS_NUMBER = 12


def get_percentage_commission():
    percentage = (100 - DEFAULT_C0MMISION) / 100.0
    return round(percentage, 2)

def create_payments():
    trans = new_transaction()
    log.info("Creating payments")

    table = Person.getAdapterClass(ICreditProvider)

    # XXX Since SQLObject SelectResults object doesn't provide an
    # index method, I need to use list here.
    card_providers = table.get_card_providers(trans)
    finance_companies = table.get_finance_companies(trans)

    destination = sysparam(trans).DEFAULT_PAYMENT_DESTINATION
    inst_settings = CardInstallmentSettings(connection=trans,
                                            payment_day=DEFAULT_PAYMENT_DAY,
                                            closing_day=DEFAULT_CLOSING_DAY)
    for provider in card_providers:
        commission = get_percentage_commission()
        general_args = dict(commission=commission, destination=destination,
                            provider=provider, connection=trans)

        DebitCardDetails(receive_days=DEFAULT_RECEIVE_DAY, **general_args)
        CreditCardDetails(installment_settings=inst_settings,
                          **general_args)
        max = MAX_INSTALLMENTS_NUMBER
        CardInstallmentsStoreDetails(installment_settings=inst_settings,
                                     max_installments_number=max,
                                     **general_args)
        CardInstallmentsProviderDetails(installment_settings=inst_settings,
                                        max_installments_number=max,
                                        **general_args)

    for provider in finance_companies:
        commission = get_percentage_commission()
        general_args = dict(commission=commission, destination=destination,
                            connection=trans, provider=provider)
        FinanceDetails(receive_days=DEFAULT_RECEIVE_DAY, **general_args)

    trans.commit()

if __name__ == '__main__':
    create_payments()

