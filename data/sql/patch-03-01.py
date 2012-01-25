from stoqlib.database.admin import register_payment_methods

def apply_patch(trans):
    register_payment_methods()
