ALTER TABLE person ADD COLUMN merged_with_id uuid REFERENCES person(id) ON UPDATE CASCADE;

