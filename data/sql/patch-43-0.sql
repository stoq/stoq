-- #3077: Implementar wizard para abrir o processo de inventario

-- Create inventory table
CREATE TABLE inventory (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint REFERENCES transaction_entry(id),
    te_modified_id bigint REFERENCES transaction_entry(id),

    status integer CONSTRAINT valid_status CHECK (status >= 0 and status < 2),
    open_date timestamp NOT NULL,
    close_date timestamp,
    invoice_number integer CONSTRAINT positive_invoice_number CHECK (invoice_number > 0  and invoice_number < 999999),
    branch_id bigint NOT NULL REFERENCES person_adapt_to_branch(id)
);


-- Create inventory_item table
CREATE TABLE inventory_item (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint REFERENCES transaction_entry(id),
    te_modified_id bigint REFERENCES transaction_entry(id),

    product_id bigint NOT NULL REFERENCES product(id),
    recorded_quantity numeric(10,2) CONSTRAINT positive_recorded_quantity CHECK (recorded_quantity >= 0),
    actual_quantity numeric(10,2) CONSTRAINT positive_actual_quantity CHECK (actual_quantity >= 0),
    inventory_id bigint NOT NULL REFERENCES inventory(id),
    reason text,
    cfop_data_id bigint REFERENCES cfop_data(id)
);
