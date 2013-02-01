from stoqlib.database.properties import UnicodeCol, BoolCol, PercentCol, IntCol
from stoqlib.migration.parameter import get_parameter
from stoqlib.migration.domainv1 import Domain


class PaymentMethod(Domain):
    __storm_table__ = 'payment_method'
    method_name = UnicodeCol()
    is_active = BoolCol(default=True)
    description = UnicodeCol()
    daily_penalty = PercentCol(default=0)
    interest = PercentCol(default=0)
    payment_day = IntCol(default=None)
    closing_day = IntCol(default=None)
    max_installments = IntCol(default=1)
    destination_account_id = IntCol()


def apply_patch(store):
    # This might run on an empty database so make sure we have
    # the imbalance account created

    account = int(get_parameter(store, u'IMBALANCE_ACCOUNT'))
    # There is no parameter yet. This means the database is brand new. No need
    # to register the new payment now, since it will be created by
    # initialize_system
    if not account:
        return

    method = store.find(PaymentMethod, method_name=u'online').one()
    if not method:
        PaymentMethod(store=store,
                      method_name=u'online',
                      destination_account_id=account,
                      max_installments=12)
