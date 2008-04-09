-- #3090: Implementar controle para produtos retidos

-- add cfop column in product_retention_history table
ALTER TABLE product_retention_history
    ADD COLUMN cfop_id bigint REFERENCES cfop_data(id),
    ADD COLUMN retention_date timestamp;

-- rename quantity_retended to quantity_retained (product_history table)
ALTER TABLE product_history RENAME COLUMN quantity_retended TO quantity_retained;
