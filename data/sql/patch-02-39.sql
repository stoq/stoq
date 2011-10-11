
CREATE TABLE product_quality_test (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    product_id bigint REFERENCES product(id),
    test_type integer,
    description text,
    success_value text
);

CREATE TABLE production_produced_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    production_item_id bigint REFERENCES production_item(id),
    produced_by_id bigint REFERENCES person_adapt_to_user(id),
    produced_date timestamp,
    serial_number text,
    entered_stock boolean,
    test_passed boolean
);

ALTER TABLE production_order DROP CONSTRAINT valid_status;
ALTER TABLE production_order ADD CONSTRAINT valid_statuos
     CHECK (status >= 0 AND status < 5);

CREATE TABLE production_item_quality_result (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    produced_item_id bigint REFERENCES production_produced_item(id),
    quality_test_id bigint REFERENCES product_quality_test(id),
    tested_by_id bigint REFERENCES person_adapt_to_user(id),
    tested_date timestamp,

    result_value text,
    test_passed boolean
);

