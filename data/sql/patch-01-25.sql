-- # 4037: Wizard de abertura de produção

ALTER TABLE production_order ADD COLUMN expected_start_date timestamp;
ALTER TABLE production_order ADD COLUMN start_date timestamp;

CREATE TABLE production_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    quantity numeric(10, 2) CONSTRAINT positive_quantity CHECK  (quantity >= 0),
    product_id bigint REFERENCES product(id),
    order_id bigint REFERENCES production_order(id)
);


CREATE TABLE production_material (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    needed numeric(10, 2) CONSTRAINT positive_quantity CHECK (needed > 0),
    consumed numeric(10, 2) DEFAULT 0 CONSTRAINT positive_consumed CHECK (consumed >= 0),
    allocated numeric(10, 2) DEFAULT 0 CONSTRAINT positive_allocated CHECK (allocated >= 0),
    to_purchase numeric(10, 2) CONSTRAINT positive_purchase_quantity CHECK (to_purchase >= 0),
    to_make numeric(10, 2) CONSTRAINT positive_make_quantity CHECK (to_make >= 0),
    lost numeric(10, 2) DEFAULT 0 CONSTRAINT positive_lost CHECK (lost >= 0),


    order_id bigint REFERENCES production_order(id),
    product_id bigint REFERENCES product(id)
);

CREATE TABLE production_service (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    quantity numeric(10, 2) CONSTRAINT positive_quantity CHECK  (quantity >= 0),
    service_id bigint REFERENCES service(id),
    order_id bigint REFERENCES production_order(id)
);
