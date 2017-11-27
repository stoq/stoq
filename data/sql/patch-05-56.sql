ALTER TABLE stock_decrease_item
    ADD COLUMN delivery_id uuid REFERENCES delivery(id) ON UPDATE CASCADE;

ALTER TABLE delivery
    ADD COLUMN invoice_id uuid REFERENCES invoice(id) ON UPDATE CASCADE;

UPDATE delivery SET invoice_id = sale.invoice_id FROM sale, sale_item
    WHERE sale.id = sale_item.sale_id AND delivery.service_item_id = sale_item.id;

ALTER TABLE delivery DROP COLUMN service_item_id;
