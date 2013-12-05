ALTER TABLE loan_item
	ADD COLUMN base_price numeric(20, 2) 
	CONSTRAINT positive_base_price CHECK (base_price >= 0);

UPDATE loan_item SET base_price = price;

ALTER TABLE loan ADD COLUMN client_category_id uuid REFERENCES client_category(id) ON UPDATE CASCADE;
