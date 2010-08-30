-- Sale Tansporter (for NFe)

ALTER TABLE sale ADD COLUMN transporter_id bigint
	REFERENCES person_adapt_to_transporter(id);
