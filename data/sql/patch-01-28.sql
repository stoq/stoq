-- #

ALTER TABLE production_item ADD COLUMN produced numeric(10, 2) DEFAULT 0
    CONSTRAINT positive_produced CHECK (produced >= 0);

