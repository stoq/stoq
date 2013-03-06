# -*- coding: utf-8 -*-
# 5412: Add quantity_decreased column on sale_item

import decimal

from stoqlib.database.properties import IntCol, QuantityCol
from stoqlib.migration.domainv2 import Domain


class ReturnedSaleItem(Domain):
    __storm_table__ = 'returned_sale_item'

    quantity = QuantityCol()
    sale_item_id = IntCol()


class SaleItem(Domain):
    __storm_table__ = 'sale_item'

    quantity = QuantityCol()
    quantity_decreased = QuantityCol()
    sale_id = IntCol()

    @property
    def returned_quantity(self):
        returned_items = self.store.find(ReturnedSaleItem,
                                         sale_item_id=self.id)
        return (returned_items.sum(ReturnedSaleItem.quantity) or
                decimal.Decimal('0'))


class Sale(Domain):
    __storm_table__ = 'sale'

    STATUS_CONFIRMED = 1
    STATUS_PAID = 2

    status = IntCol()


_SQL_CMD = """
  ALTER TABLE sale_item
    ADD COLUMN quantity_decreased numeric(20, 3) DEFAULT 0
      CONSTRAINT valid_quantity_decreased CHECK (quantity_decreased <= quantity);
  """


def apply_patch(store):
    store.execute(_SQL_CMD)
    for sale_item in store.find(SaleItem):
        sale = store.find(Sale, id=sale_item.sale_id).one()
        if sale.status not in [Sale.STATUS_CONFIRMED, Sale.STATUS_PAID]:
            continue

        # For confirmed and paid sales, quantity_returned should be equal to
        # quantity, except when they have partial devolutions, since they alter
        # the quantity_decreased too.
        sale_item.quantity_decreased = (sale_item.quantity -
                                        sale_item.returned_quantity)
