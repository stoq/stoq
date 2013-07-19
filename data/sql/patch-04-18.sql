-- Add batch control for products

CREATE TABLE storable_batch (
    id serial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    batch_number text UNIQUE NOT NULL,
    create_date timestamp NOT NULL,
    expire_date timestamp,
    notes text,

    storable_id bigint NOT NULL REFERENCES storable(id) ON UPDATE CASCADE
);

ALTER TABLE storable ADD COLUMN is_batch boolean DEFAULT False;
ALTER TABLE sale_item ADD batch_id bigint REFERENCES storable_batch(id) ON UPDATE CASCADE;
ALTER TABLE loan_item ADD batch_id bigint REFERENCES storable_batch(id) ON UPDATE CASCADE;
ALTER TABLE receiving_order_item ADD batch_id bigint REFERENCES storable_batch(id) ON UPDATE CASCADE;
ALTER TABLE returned_sale_item ADD batch_id bigint REFERENCES storable_batch(id) ON UPDATE CASCADE;
ALTER TABLE stock_decrease_item ADD batch_id bigint REFERENCES storable_batch(id) ON UPDATE CASCADE;
ALTER TABLE transfer_order_item ADD batch_id bigint REFERENCES storable_batch(id) ON UPDATE CASCADE;
ALTER TABLE work_order_item ADD batch_id bigint REFERENCES storable_batch(id) ON UPDATE CASCADE;
ALTER TABLE inventory_item ADD batch_id bigint REFERENCES storable_batch(id) ON UPDATE CASCADE;

ALTER TABLE product_stock_item ADD batch_id bigint REFERENCES storable_batch(id) ON UPDATE CASCADE;
ALTER TABLE product_stock_item ADD UNIQUE (branch_id, storable_id, batch_id);
