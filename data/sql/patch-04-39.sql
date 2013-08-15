-- Remove not null contraint from transfer_order_item

ALTER TABLE transfer_order_item ALTER transfer_order_id DROP NOT NULL;
