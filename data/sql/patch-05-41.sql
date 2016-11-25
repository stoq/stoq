ALTER TABLE loan_item ADD COLUMN pis_info_id uuid DEFAULT NULL;
ALTER TABLE loan_item ADD CONSTRAINT loan_item_pis_info_id_fkey
    FOREIGN KEY (pis_info_id) REFERENCES invoice_item_pis (id) ON UPDATE CASCADE;

ALTER TABLE loan_item ADD COLUMN cofins_info_id uuid DEFAULT NULL;
ALTER TABLE loan_item ADD CONSTRAINT loan_item_cofins_info_id_fkey
    FOREIGN KEY (cofins_info_id) REFERENCES invoice_item_cofins (id) ON UPDATE CASCADE;
