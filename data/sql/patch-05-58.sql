ALTER TABLE work_order
    ADD COLUMN wait_date timestamp,
    ADD COLUMN in_progress_date timestamp,
    ADD COLUMN deliver_date timestamp,
    ADD COLUMN client_informed_date timestamp;

ALTER TABLE work_order_item
    ADD COLUMN purchase_item_id uuid REFERENCES purchase_item(id) ON UPDATE CASCADE;

ALTER TABLE purchase_order
    ADD COLUMN work_order_id uuid REFERENCES work_order(id) ON UPDATE CASCADE;

