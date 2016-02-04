ALTER TABLE product ADD COLUMN is_package BOOLEAN DEFAULT FALSE;

-- XXX Adding columns from a future patch, wich is related to this
ALTER TABLE sale_item
    ADD COLUMN parent_item_id uuid REFERENCES sale_item(id) ON UPDATE CASCADE;

ALTER TABLE purchase_item
    ADD COLUMN parent_item_id uuid REFERENCES purchase_item(id) ON UPDATE CASCADE;
