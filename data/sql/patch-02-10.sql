

ALTER TABLE sale_item ADD COLUMN ipi_info_id bigint REFERENCES
    sale_item_ipi(id);
