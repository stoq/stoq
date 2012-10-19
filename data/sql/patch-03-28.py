from stoqlib.database.admin import register_payment_methods
from stoqlib.domain.person import Person
from stoqlib.domain.sale import Sale
from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.lib.parameters import sysparam


def apply_patch(trans):
    trans.query("""
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
    for sale_id, person_id, invoice_number, reason, penalty in trans.queryAll(
        """SELECT sale_id, responsible_id, invoice_number, reason, penalty_value
               FROM renegotiation_data;"""):
        sale = Sale.get(sale_id, trans)
        person = Person.get(person_id, trans)
        if invoice_number is not None:
            # invoice_number can be duplicated, since it wasn't unique before
            # First come, first served. Others will have no invoice number
            if invoice_number in invoice_numbers:
                invoice_number = None
            invoice_numbers.add(invoice_number)
        returned_sale = ReturnedSale(
            connection=trans,
            return_date=sale.return_date,
            invoice_number=invoice_number,
            responsible=person.login_user,
            reason=reason,
            branch=sale.branch,
            sale=sale,
            )
        for sale_item in sale.get_items():
            ReturnedSaleItem(
                connection=trans,
                sale_item=sale_item,
                returned_sale=returned_sale,
                quantity=sale_item.quantity,
                )

    trans.query("DROP TABLE renegotiation_data;")

    account = sysparam(trans).IMBALANCE_ACCOUNT
    # Only do that if IMBALANCE_ACCOUNT is already registered. Else, the
    # database is brand new and payment method will be created later.
    if account:
        # Register the new payment method, 'trade'
        register_payment_methods(trans)
