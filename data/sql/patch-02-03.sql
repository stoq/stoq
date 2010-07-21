--Create client_category

CREATE TABLE client_category (
	id serial NOT NULL PRIMARY KEY,
	te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
	te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
	name text UNIQUE
);

ALTER TABLE person_adapt_to_client ADD COLUMN category_id bigint
	REFERENCES client_category(id);
