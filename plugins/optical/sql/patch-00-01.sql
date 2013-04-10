-- Initial schema for optical stores plugin.

CREATE TABLE optical_work_order (
    id bigserial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),

    work_order_id bigint UNIQUE REFERENCES work_order(id) ON UPDATE CASCADE,
    prescription_date timestamp,

    -- TODO: Figure out if this space is enough
    od_esferico numeric(5, 2),

    oe_esferico numeric(5, 2)

);
