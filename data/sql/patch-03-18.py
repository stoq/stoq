from kiwi.python import strip_accents
from stoqlib.migration.domainv1 import Domain
from stoqlib.database.properties import UnicodeCol


class ProductManufacturer(Domain):
    __storm_table__ = 'product_manufacturer'
    name = UnicodeCol()


def apply_patch(store):
    store.execute("""
        CREATE TABLE product_manufacturer (
           id serial NOT NULL PRIMARY KEY,
           te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
           te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
           name text UNIQUE
        );

        ALTER TABLE product ADD COLUMN manufacturer_id bigint
            REFERENCES product_manufacturer(id);
          """)

    alikes = {}
    for name, in store.execute("""SELECT DISTINCT(manufacturer) FROM product
                                  ORDER BY manufacturer;""").get_all():
        if not name or not name.strip():
            continue

        # If a manufacturer with a similar name have already been created, use
        # that instead.
        key = strip_accents(name.strip().lower())
        if key in alikes:
            m = alikes[key]
        else:
            m = ProductManufacturer(store=store, name=name.strip())
            alikes[key] = m

        store.execute("""
            UPDATE product set manufacturer_id = ? WHERE manufacturer = ?
        """, (m.id, name))

    store.execute("""ALTER TABLE product DROP COLUMN manufacturer;""")
