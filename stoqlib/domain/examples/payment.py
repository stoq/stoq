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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):        Evandro Vale Miquelito     <evandro@async.com.br>
##
"""Create simple payments to an example database"""

import gettext
from  random import randint

from stoqlib.lib.runtime import new_transaction, print_msg
from stoqlib.lib.parameters import sysparam
from stoqlib.domain.interfaces import (ICreditProvider, ICheckPM, IBillPM)
from stoqlib.domain.person import Person
from stoqlib.domain.payment.methods import (CardInstallmentSettings,
                                            DebitCardDetails, 
                                            CreditCardDetails,
                                            CardInstallmentsStoreDetails,
                                            CardInstallmentsProviderDetails,
                                            FinanceDetails)

_ = gettext.gettext



#
# Main
#



DEFAULT_CLOSING_DAY = 12
DEFAULT_PAYMENT_DAY = 15
# This means 1% of commission to 10 %
DEFAULT_C0MMISION_RANGE = 1, 10

DEFAULT_RECEIVE_DAY = 5

MAX_INSTALLMENTS_NUMBER = 12


def get_percentage_commission():
    random_commission = randint(*DEFAULT_C0MMISION_RANGE)
    percentage = (100 - random_commission) / 100.0
    return round(percentage, 2)

def create_payments():
    conn = new_transaction()
    print_msg("Creating payments... ", break_line=False)

    table = Person.getAdapterClass(ICreditProvider)

    # XXX Since SQLObject SelectResults object doesn't provide an
    # index method, I need to use list here.
    card_providers = table.get_card_providers(conn)
    finance_companies = table.get_finance_companies(conn)

    destination = sysparam(conn).DEFAULT_PAYMENT_DESTINATION
    inst_settings = CardInstallmentSettings(connection=conn,
                                            payment_day=DEFAULT_PAYMENT_DAY,
                                            closing_day=DEFAULT_CLOSING_DAY)
    for provider in card_providers:
        commission = get_percentage_commission()
        general_args = dict(commission=commission, destination=destination,
                            provider=provider, connection=conn)

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
                            connection=conn, provider=provider)
        FinanceDetails(receive_days=DEFAULT_RECEIVE_DAY, **general_args)


    pm = sysparam(conn).BASE_PAYMENT_METHOD
    for iface in [ICheckPM, IBillPM]:
        method = iface(pm, connection=conn)
        method.max_installments_number = MAX_INSTALLMENTS_NUMBER
        
    conn.commit()
    print_msg("done.")

if __name__ == '__main__':
    create_payments()

