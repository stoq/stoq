-- #2244: Implementar wizard para cotacao de compras

ALTER TABLE purchase_order_adapt_to_quote RENAME COLUMN original_id TO purchase_id;
ALTER TABLE purchase_order_adapt_to_quote RENAME TO quotation;
ALTER TABLE purchase_order_adapt_to_quote_id_seq RENAME TO quotation_id_seq;
