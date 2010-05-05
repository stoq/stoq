-- Creation of person_adapt_to_publisher and product_adapt_to_book tables.


CREATE TABLE person_adapt_to_publisher (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES person(id),
    status integer NOT NULL CONSTRAINT valid_status CHECK (status >= 0 AND status <= 1)

);
