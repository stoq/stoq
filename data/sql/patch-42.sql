-- #3671 Add fiscal information about sales.

ALTER TABLE paulista_invoice RENAME TO fiscal_sale_history;
ALTER TABLE paulista_invoice_id_seq RENAME TO fiscal_sale_history_id_seq;

ALTER TABLE fiscal_sale_history ADD COLUMN coo integer;
ALTER TABLE fiscal_sale_history ADD COLUMN document_counter integer;

