from stoqlib.domain.uiform import create_default_forms

def apply_patch(trans):
    trans.query("""
CREATE TABLE ui_form (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    form_name text UNIQUE
);

CREATE TABLE ui_field (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    field_name text,
    mandatory boolean,
    visible boolean,
    ui_form_id bigint REFERENCES ui_form(id)
);""")

    create_default_forms(trans)
