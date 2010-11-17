

ALTER TABLE sellable ADD COLUMN default_sale_cfop_id bigint REFERENCES
    cfop_data(id);

ALTER TABLE sale_item ADD COLUMN cfop_id bigint REFERENCES
    cfop_data(id);
