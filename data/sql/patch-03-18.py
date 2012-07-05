from kiwi.python import strip_accents
from stoqlib.domain.product import ProductManufacturer


def apply_patch(trans):
    trans.query("""
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
    for name, in trans.queryAll("""SELECT DISTINCT(manufacturer) FROM product
                                    ORDER BY manufacturer;"""):
        if not name or not name.strip():
            continue

        # If a manufacturer with a similar name have already been created, use
        # that instead.
        key = strip_accents(name.strip().lower())
        if key in alikes:
            m = alikes[key]
        else:
            m = ProductManufacturer(connection=trans, name=name.strip())
            alikes[key] = m

        trans.query("""
            UPDATE product set manufacturer_id = %s WHERE manufacturer = %s
        """ % (m.id, trans.sqlrepr(name)))

    trans.query("""ALTER TABLE product DROP COLUMN manufacturer;""")
