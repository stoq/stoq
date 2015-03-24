ALTER TABLE sale_item_icms RENAME TO invoice_item_icms;
ALTER TABLE sale_item_ipi RENAME TO invoice_item_ipi;

ALTER INDEX sale_item_icms_pkey RENAME TO invoice_item_icms_pkey;
ALTER INDEX sale_item_icms_te_id_key RENAME TO invoice_item_icms_te_id_key;
ALTER TABLE invoice_item_icms DROP CONSTRAINT sale_item_icms_te_id_fkey;
ALTER TABLE invoice_item_icms ADD CONSTRAINT invoice_item_icms_te_id_fkey
    FOREIGN KEY (te_id) REFERENCES transaction_entry (id);

ALTER INDEX sale_item_ipi_pkey RENAME TO invoice_item_ipi_pkey;
ALTER INDEX sale_item_ipi_te_id_key RENAME TO invoice_item_ipi_te_id_key;
ALTER TABLE invoice_item_ipi DROP CONSTRAINT sale_item_ipi_te_id_fkey;
ALTER TABLE invoice_item_ipi ADD CONSTRAINT invoice_item_ipi_te_id_fkey
    FOREIGN KEY (te_id) REFERENCES transaction_entry (id);

CREATE TYPE invoice_type AS ENUM ('in', 'out');

CREATE TABLE invoice (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) default new_te(),
    invoice_number integer NOT NULL,
    operation_nature text,
    invoice_type invoice_type NOT NULL,
    key text
);
CREATE RULE update_te AS ON UPDATE TO invoice DO ALSO SELECT update_te(old.te_id);
