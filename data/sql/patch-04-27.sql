-- Relate work order items with its sale item

ALTER TABLE work_order_item ADD COLUMN sale_item_id uuid REFERENCES sale_item(id) ON UPDATE CASCADE;
