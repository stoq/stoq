

ALTER TABLE sale_item ADD COLUMN ipi_info_id bigint REFERENCES
    sale_item_ipi(id);

ALTER TABLE product_ipi_template ADD COLUMN calculo integer;
ALTER TABLE sale_item_ipi ADD COLUMN calculo integer;

ALTER TABLE sale_item_icms ADD COLUMN bc_include_ipi boolean
    DEFAULT True;
ALTER TABLE sale_item_icms ADD COLUMN bc_st_include_ipi boolean
    DEFAULT True;

ALTER TABLE product_icms_template ADD COLUMN bc_include_ipi boolean
    DEFAULT True;
ALTER TABLE product_icms_template ADD COLUMN bc_st_include_ipi boolean
    DEFAULT True;


