ALTER TABLE sale DROP COLUMN invoice_number;
ALTER TABLE sale DROP COLUMN operation_nature;
ALTER TABLE returned_sale DROP COLUMN invoice_number;
ALTER TABLE transfer_order DROP COLUMN invoice_number;
ALTER TABLE stock_decrease DROP COLUMN invoice_number;
