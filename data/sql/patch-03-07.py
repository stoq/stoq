from stoqlib.lib.parameters import sysparam
from stoqlib.database.admin import register_payment_methods

def apply_patch(trans):
    # This might run on an empty database so make sure we have
    # the imbalance account created

    account = sysparam(trans).IMBALANCE_ACCOUNT
    # There is no parameter yet. This means the database is brand new. No need
    # to register the new payment now, since it will be created by
    # initialize_system
    if not account:
        return

    register_payment_methods(trans)
