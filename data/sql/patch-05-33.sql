ALTER TABLE product ADD COLUMN is_package BOOLEAN DEFAULT FALSE;

-- XXX Adding columns from a future patch, wich is related to this
ALTER TABLE sale_item
    ADD COLUMN parent_item_id uuid REFERENCES sale_item(id) ON UPDATE CASCADE;

ALTER TABLE purchase_item
    ADD COLUMN parent_item_id uuid REFERENCES purchase_item(id) ON UPDATE CASCADE;

ALTER TABLE returned_sale_item
    ADD COLUMN parent_item_id uuid REFERENCES returned_sale_item(id) ON UPDATE CASCADE;

ALTER TABLE receiving_order_item
    ADD COLUMN parent_item_id uuid REFERENCES receiving_order_item(id) ON UPDATE CASCADE;
