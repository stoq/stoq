-- Compras - produtos em trânsito - inserir data estimada.

ALTER TABLE product_supplier_info
    ADD COLUMN lead_time integer DEFAULT 1
    CONSTRAINT positive_lead_time CHECK (lead_time > 0);

ALTER TABLE purchase_item
    ADD COLUMN expected_receival_date timestamp;
