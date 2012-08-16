ALTER TABLE client_category ADD COLUMN max_discount numeric(10,2)
  DEFAULT 0
  CONSTRAINT valid_max_discount CHECK (max_discount BETWEEN 0 AND 100);
