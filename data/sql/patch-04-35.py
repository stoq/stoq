# -*- coding: utf-8 -*-

from storm.expr import Join, Ne

from stoqlib.database.properties import UnicodeCol, DateTimeCol, IdCol
from stoqlib.lib.dateutils import localnow
from stoqlib.migration.domainv3 import Domain


class Sale(Domain):
    __storm_table__ = 'sale'

    open_date = DateTimeCol()
    notes = UnicodeCol()
    salesperson_id = IdCol()


class SaleComment(Domain):
    __storm_table__ = 'sale_comment'

    date = DateTimeCol(default_factory=localnow)
    comment = UnicodeCol()
    author_id = IdCol()
    sale_id = IdCol()


class SalesPerson(Domain):
    __storm_table__ = 'sales_person'

    person_id = IdCol()


class LoginUser(Domain):
    __storm_table__ = 'login_user'

    person_id = IdCol()


class Person(Domain):
    __storm_table__ = 'person'


def apply_patch(store):
    store.execute("""
        CREATE TABLE sale_comment (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
            te_id bigint UNIQUE REFERENCES transaction_entry(id),

            date timestamp,
            comment text,
            sale_id uuid NOT NULL REFERENCES sale(id) ON UPDATE CASCADE,
            author_id uuid NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE
        );
    """)

    tables = [Sale,
              Join(SalesPerson, Sale.salesperson_id == SalesPerson.id),
              Join(Person, SalesPerson.person_id == Person.id),
              Join(LoginUser, LoginUser.person_id == Person.id)]

    for sale, user in store.using(*tables).find((Sale, LoginUser),
                                                Ne(Sale.notes, None)):
        SaleComment(store=store, sale_id=sale.id, author_id=user.id,
                    date=sale.open_date, comment=sale.notes)

    # Just a precaution: Flush to make sure we do the migration before
    # dropping the column
    store.flush()
    store.execute("ALTER TABLE sale DROP COLUMN notes;")
