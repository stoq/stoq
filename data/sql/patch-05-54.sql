ALTER TABLE receiving_order ADD COLUMN invoice_key TEXT;
ALTER TABLE stock_decrease
    ADD COLUMN receiving_order_id UUID REFERENCES receiving_order(id) ON UPDATE CASCADE,
    ADD COLUMN referenced_invoice_key TEXT;
ALTER TABLE stock_decrease_item
    ADD COLUMN receiving_order_item_id UUID REFERENCES receiving_order_item(id) ON UPDATE CASCADE;
