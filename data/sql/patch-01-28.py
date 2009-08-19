# -*- coding: utf-8 -*-

# Bug 4039: Adicionar custo médio ao estoque

from stoqlib.domain.receiving import ReceivingOrder
from stoqlib.domain.sale import Sale
from stoqlib.domain.product import Product
from stoqlib.domain.transfer import TransferOrder
from stoqlib.domain.interfaces import IStorable

def apply_patch(trans):
    trans.query("""ALTER TABLE sale_item ADD COLUMN average_cost
                 numeric(10,2) DEFAULT 0;""")

    # data migration
    orders = list(ReceivingOrder.select(connection=trans))
    sales = list(Sale.select(connection=trans))
    transfers = list(TransferOrder.select(connection=trans))

    timeline = []
    timeline.extend([(o.receival_date, o) for o in orders])
    timeline.extend([(o.confirm_date, o) for o in sales])
    timeline.extend([(o.receival_date, o) for o in transfers])
    timeline.sort()

    for date, order in timeline:
        if isinstance(order, ReceivingOrder):
            for item in order.get_items():
                storable = IStorable(item.sellable.product, None)
                if storable is None:
                    continue

                stock = storable.get_stock_item(order.branch)
                stock.update_cost(item.quantity, item.cost)

        elif isinstance(order, Sale):
            for item in order.get_items():
                storable = IStorable(item.sellable.product, None)
                if storable is None:
                    continue

                stock = storable.get_stock_item(order.branch)
                item.average_cost = stock.stock_cost

        elif isinstance(order, TransferOrder):
            for item in order.get_items():
                storable = IStorable(item.sellable.product, None)
                if storable is None:
                    continue

                from_stock = storable.get_stock_item(order.destination_branch)
                to_stock = storable.get_stock_item(order.destination_branch)

                to_stock.update_cost(item.quantity, from_stock.stock_cost)


