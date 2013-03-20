import datetime
from storm.references import Reference
from storm.store import AutoReload

from stoqlib.database.properties import (UnicodeCol, BoolCol, PercentCol,
                                         IntCol, QuantityCol, PriceCol, DateTimeCol)

from stoqlib.migration.domainv1 import Domain
from stoqlib.migration.parameter import get_parameter


class LoginUser(Domain):
    __storm_table__ = 'login_user'
    person_id = IntCol()


class Branch(Domain):
    __storm_table__ = 'branch'


class Person(Domain):
    __storm_table__ = 'person'

Person.login_user = Reference(Person.id, LoginUser.person_id, on_remote=True)


class PaymentMethod(Domain):
    __storm_table__ = 'payment_method'
    method_name = UnicodeCol()
    is_active = BoolCol(default=True)
    daily_penalty = PercentCol(default=0)
    interest = PercentCol(default=0)
    payment_day = IntCol(default=None)
    closing_day = IntCol(default=None)
    max_installments = IntCol(default=1)
    destination_account_id = IntCol()


class SaleItem(Domain):
    __storm_table__ = 'sale_item'
    quantity = QuantityCol()
    sale_id = IntCol()


class ReturnedSaleItem(Domain):
    __storm_table__ = 'returned_sale_item'
    quantity = QuantityCol(default=0)
    price = PriceCol()
    sale_item_id = IntCol()
    sale_item = Reference(sale_item_id, SaleItem.id)
    sellable_id = IntCol()
    returned_sale_id = IntCol()


class Sale(Domain):
    __storm_table__ = 'sale'
    return_date = DateTimeCol(default=None)
    branch_id = IntCol()
    branch = Reference(branch_id, Branch.id)

    def get_items(self):
        return self.store.find(SaleItem, sale_id=self.id).order_by(SaleItem.id)


class ReturnedSale(Domain):
    __storm_table__ = 'returned_sale'
    identifier = IntCol(default=AutoReload)
    return_date = DateTimeCol(default_factory=datetime.datetime.now)
    invoice_number = IntCol(default=None)
    reason = UnicodeCol(default=u'')

    sale_id = IntCol()
    sale = Reference(sale_id, Sale.id)

    new_sale_id = IntCol()
    new_sale = Reference(new_sale_id, Sale.id)

    responsible_id = IntCol()
    responsible = Reference(responsible_id, LoginUser.id)
    branch_id = IntCol()
    branch = Reference(branch_id, Branch.id)


def apply_patch(store):
    store.execute("""
        CREATE TABLE returned_sale (
            id serial NOT NULL PRIMARY KEY,
            te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
            te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

            identifier serial NOT NULL,
            return_date timestamp,
            reason text,
            invoice_number integer CONSTRAINT valid_invoice_number
                CHECK (invoice_number > 0 AND invoice_number <= 999999999)
                DEFAULT NULL UNIQUE,
            responsible_id bigint REFERENCES login_user(id) ON UPDATE CASCADE,
            branch_id bigint REFERENCES branch(id) ON UPDATE CASCADE,
            sale_id bigint REFERENCES sale(id) ON UPDATE CASCADE,
            new_sale_id bigint UNIQUE REFERENCES sale(id) ON UPDATE CASCADE
        );

        CREATE TABLE returned_sale_item (
            id serial NOT NULL PRIMARY KEY,
            te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
            te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

            quantity numeric(20, 3) CONSTRAINT positive_quantity
                CHECK (quantity >= 0),
            price numeric(20, 2) CONSTRAINT positive_price
                CHECK (price >= 0),
            sellable_id bigint REFERENCES sellable(id) ON UPDATE CASCADE,
            sale_item_id bigint REFERENCES sale_item(id) ON UPDATE CASCADE,
            returned_sale_id bigint REFERENCES returned_sale(id) ON UPDATE CASCADE
        );
        """)

    # Migrate all renegotiation_data to returned_sale
    invoice_numbers = set()
    for sale_id, person_id, invoice_number, reason, penalty in store.execute(
        """SELECT sale_id, responsible_id, invoice_number, reason, penalty_value
               FROM renegotiation_data;""").get_all():
        sale = Sale.get(sale_id, store)
        person = Person.get(person_id, store)
        if invoice_number is not None:
            # invoice_number can be duplicated, since it wasn't unique before
            # First come, first served. Others will have no invoice number
            if invoice_number in invoice_numbers:
                invoice_number = None
            invoice_numbers.add(invoice_number)
        returned_sale = ReturnedSale(
            store=store,
            return_date=sale.return_date,
            invoice_number=invoice_number,
            responsible=person.login_user,
            reason=reason,
            branch=sale.branch,
            sale=sale,
        )
        for sale_item in sale.get_items():
            ReturnedSaleItem(
                store=store,
                sale_item=sale_item,
                returned_sale_id=returned_sale.id,
                quantity=sale_item.quantity,
            )

    store.execute("DROP TABLE renegotiation_data;")

    account = int(get_parameter(store, u'IMBALANCE_ACCOUNT'))
    # Only do that if IMBALANCE_ACCOUNT is already registered. Else, the
    # database is brand new and payment method will be created later.
    if account:
        # Register the new payment method, 'trade'
        method = store.find(PaymentMethod, method_name=u'trade').one()
        if not method:
            PaymentMethod(store=store,
                          method_name=u'trade',
                          destination_account_id=account,
                          max_installments=12)
