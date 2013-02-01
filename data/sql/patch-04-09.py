from storm.expr import And
from storm.references import Reference

from stoqlib.database.expr import TransactionTimestamp
from stoqlib.database.properties import (PriceCol, UnicodeCol, IntCol,
                                         QuantityCol, DateTimeCol)
from stoqlib.migration.domainv2 import Domain


class Sellable(Domain):
    __storm_table__ = 'sellable'

    description = UnicodeCol(default=u'')


class Product(Domain):
    __storm_table__ = 'product'

    sellable_id = IntCol()
    sellable = Reference(sellable_id, Sellable.id)


class Storable(Domain):
    __storm_table__ = 'storable'

    product_id = IntCol()
    product = Reference(product_id, Product.id)


class ProductStockItem(Domain):
    __storm_table__ = 'product_stock_item'

    stock_cost = PriceCol(default=0)
    quantity = QuantityCol(default=0)
    storable_id = IntCol()
    storable = Reference(storable_id, Storable.id)


class StockTransactionHistory(Domain):
    __storm_table__ = 'stock_transaction_history'

    TYPE_IMPORTED = 15
    product_stock_item_id = IntCol()
    stock_cost = PriceCol()
    quantity = QuantityCol()
    responsible_id = IntCol()
    date = DateTimeCol()
    object_id = IntCol()
    type = IntCol()


def apply_patch(store):
    store.execute("""
        CREATE TABLE stock_transaction_history(
            id serial NOT NULL PRIMARY KEY,
            te_id bigint UNIQUE REFERENCES transaction_entry(id),
            date timestamp,
            stock_cost numeric(20, 8) CONSTRAINT positive_cost
                CHECK (stock_cost >= 0),
            quantity numeric(20, 3),
            type int CONSTRAINT type_range CHECK (type >= 0 and type <= 15),
            object_id bigint,
            responsible_id bigint NOT NULL REFERENCES login_user(id)
                ON UPDATE CASCADE,
            product_stock_item_id bigint NOT NULL REFERENCES product_stock_item(id)
                ON UPDATE CASCADE ON DELETE CASCADE
        );""")

    res = store.execute("""SELECT id FROM login_user WHERE
                           username='admin'""").get_one()
    if not res:
        res = store.execute("""SELECT MIN(id) FROM login_user""").get_one()
    if res:
        user_id = res[0]

    # If the database is being created, there is no user and no stock items,
    # so this for will not be executed.
    for (item, sellable) in store.find((ProductStockItem, Sellable),
                                       And(ProductStockItem.storable_id == Storable.id,
                                           Storable.product_id == Product.id,
                                           Product.sellable_id == Sellable.id)):
        StockTransactionHistory(product_stock_item_id=item.id,
                                date=TransactionTimestamp(),
                                stock_cost=item.stock_cost,
                                quantity=item.quantity,
                                responsible_id=user_id,
                                type=StockTransactionHistory.TYPE_IMPORTED,
                                store=store)
