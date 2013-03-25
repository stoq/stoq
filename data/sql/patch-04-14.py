# -*- coding: utf-8 -*-

from stoqlib.database.properties import UnicodeCol, BoolCol, PercentCol, IntCol
from stoqlib.migration.parameter import get_parameter
from stoqlib.migration.domainv2 import Domain


class PaymentMethod(Domain):
    __storm_table__ = 'payment_method'

    method_name = UnicodeCol()
    is_active = BoolCol(default=True)
    daily_interest = PercentCol(default=0)
    penalty = PercentCol(default=0)
    payment_day = IntCol(default=None)
    closing_day = IntCol(default=None)
    max_installments = IntCol(default=1)
    destination_account_id = IntCol()


# Add the 'credit' payment method when we are updating the database,
# otherwise the payment method will be added automaticaly when setting up the
# system.

def apply_patch(store):
    # This might run on an empty database so make sure we have
    # the imbalance account created

    destination_account = get_parameter(store, u'IMBALANCE_ACCOUNT')
    # There is no parameter yet. This means the database is brand new. No need
    # to register the new payment now, since it will be created by
    # initialize_system
    if not destination_account:
        return

    method = store.find(PaymentMethod, method_name=u'credit').one()
    if not method:
        PaymentMethod(method_name=u'credit',
                      destination_account_id=int(destination_account),
                      store=store)
