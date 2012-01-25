from stoqlib.database.admin import (register_accounts,
                                    register_payment_methods)

def apply_patch(trans):
    # This might run on an empty database so make sure we have
    # the imbalance account created
    register_accounts(trans)
    register_payment_methods(trans)
