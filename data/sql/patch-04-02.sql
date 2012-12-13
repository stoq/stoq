ALTER TABLE product_supplier_info
	ADD COLUMN supplier_code TEXT,
	ADD CONSTRAINT unique_supplier_code
		UNIQUE (supplier_id, product_id, supplier_code);
