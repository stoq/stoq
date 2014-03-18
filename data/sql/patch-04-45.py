# -*- coding: utf-8 -*-


from stoqlib.database.properties import IdCol
from stoqlib.migration.domainv3 import Domain


class ReceivingOrder(Domain):
    __storm_table__ = 'receiving_order'

    purchase_id = IdCol()


class PurchaseReceivingMap(Domain):
    __storm_table__ = 'purchase_receiving_map'

    purchase_id = IdCol()
    receiving_id = IdCol()


def apply_patch(store):
    store.execute("""
        CREATE TABLE purchase_receiving_map (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
            te_id bigint UNIQUE REFERENCES transaction_entry(id),

            purchase_id uuid REFERENCES purchase_order(id) ON UPDATE CASCADE,
            receiving_id uuid REFERENCES receiving_order(id) ON UPDATE CASCADE
        )
    """)

    for (receiving_id, purchase_id) in store.find((ReceivingOrder.id,
                                                   ReceivingOrder.purchase_id)):
        PurchaseReceivingMap(store=store, purchase_id=purchase_id,
                             receiving_id=receiving_id)

    # Just a precaution: Flush to make sure we do the migration before
    # dropping the column
    store.flush()
    store.execute("ALTER TABLE receiving_order DROP COLUMN purchase_id;")
