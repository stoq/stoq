-- Add quantity_decreased column on work_order_item

ALTER TABLE work_order_item ADD COLUMN quantity_decreased numeric(20,3) DEFAULT 0;
UPDATE work_order_item SET quantity_decreased = quantity;

-- Change type_range to accept a new type, TYPE_WORK_ORDER_RETURN_TO_STOCK (18)
ALTER TABLE stock_transaction_history
    DROP CONSTRAINT type_range;
ALTER TABLE stock_transaction_history
    ADD CONSTRAINT type_range CHECK (type >= 0 and type <= 19);
