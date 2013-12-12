ALTER TABLE stock_decrease ADD COLUMN person_id uuid REFERENCES person(id) ON UPDATE CASCADE;
