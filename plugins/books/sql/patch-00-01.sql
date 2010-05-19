-- Creation of person_adapt_to_publisher and product_adapt_to_book tables.


CREATE TABLE person_adapt_to_publisher (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES person(id),
    status integer NOT NULL CONSTRAINT valid_status CHECK (status >= 0 AND status <= 1)

);

CREATE TABLE product_adapt_to_book (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    original_id bigint UNIQUE REFERENCES product(id),

    publisher_id bigint REFERENCES person_adapt_to_publisher (id),
    author text,
    series text,
    edition text,
    subject text,
    isbn text,
    language text,
    pages integer,
    decorative_finish text,
    country text,
    synopsis text
);
