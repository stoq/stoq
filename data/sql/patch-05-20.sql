ALTER TABLE sale
    DROP CONSTRAINT IF EXISTS sale_invoice_number_key,
    ADD CONSTRAINT sale_invoice_number_branch_id_key UNIQUE (invoice_number, branch_id);

ALTER TABLE returned_sale
    DROP CONSTRAINT IF EXISTS returned_sale_invoice_number_key,
    ADD CONSTRAINT returned_sale_invoice_number_branch_id_key UNIQUE (invoice_number, branch_id);

-- Alter invoice table
ALTER TABLE invoice
    ADD COLUMN cnf text,
    ALTER COLUMN invoice_number DROP NOT NULL,
    ADD COLUMN branch_id uuid REFERENCES branch(id) ON UPDATE CASCADE,
    ADD CONSTRAINT invoice_branch_id_invoice_number_key UNIQUE (branch_id, invoice_number);

-- Add the icms_info_id and ipi_info columns
ALTER TABLE loan_item
    ADD COLUMN icms_info_id uuid REFERENCES invoice_item_icms(id) ON UPDATE CASCADE,
    ADD COLUMN ipi_info_id uuid REFERENCES invoice_item_ipi(id) ON UPDATE CASCADE;

ALTER TABLE returned_sale_item
    ADD COLUMN icms_info_id uuid REFERENCES invoice_item_icms(id) ON UPDATE CASCADE,
    ADD COLUMN ipi_info_id uuid REFERENCES invoice_item_ipi(id) ON UPDATE CASCADE;

ALTER TABLE stock_decrease_item
    ADD COLUMN icms_info_id uuid REFERENCES invoice_item_icms(id) ON UPDATE CASCADE,
    ADD COLUMN ipi_info_id uuid REFERENCES invoice_item_ipi(id) ON UPDATE CASCADE;

ALTER TABLE transfer_order_item
    ADD COLUMN icms_info_id uuid REFERENCES invoice_item_icms(id) ON UPDATE CASCADE,
    ADD COLUMN ipi_info_id uuid REFERENCES invoice_item_ipi(id) ON UPDATE CASCADE;

-- Add the 'invoice_id' column.
ALTER TABLE loan
    ADD COLUMN invoice_id uuid REFERENCES invoice(id) ON UPDATE CASCADE;

ALTER TABLE returned_sale
    ADD COLUMN invoice_id uuid REFERENCES invoice(id) ON UPDATE CASCADE;

ALTER TABLE sale
    ADD COLUMN invoice_id uuid REFERENCES invoice(id) ON UPDATE CASCADE;

ALTER TABLE stock_decrease
    ADD COLUMN invoice_id uuid REFERENCES invoice(id) ON UPDATE CASCADE;

ALTER TABLE transfer_order
    ADD COLUMN invoice_id uuid REFERENCES invoice(id) ON UPDATE CASCADE;
