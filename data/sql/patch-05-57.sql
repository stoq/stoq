ALTER TABLE product_supplier_info
    ADD COLUMN branch_id UUID REFERENCES branch(id) ON UPDATE CASCADE,
    DROP CONSTRAINT unique_supplier_code,
    ADD CONSTRAINT unique_product_supplier_code_branch UNIQUE (supplier_id, product_id, supplier_code, branch_id);
