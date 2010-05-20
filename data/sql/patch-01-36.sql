-- Add consignment, width, height, depth and weight columns in product table.

ALTER TABLE product
    ADD COLUMN consignment boolean NOT NULL DEFAULT false,
    ADD COLUMN width numeric(10, 2) CONSTRAINT positive_width CHECK (width >= 0),
    ADD COLUMN height numeric(10, 2) CONSTRAINT positive_height CHECK (height >= 0),
    ADD COLUMN depth numeric(10, 2) CONSTRAINT positive_depth CHECK (depth >= 0),
    ADD COLUMN weight numeric(10, 2) CONSTRAINT positive_weight CHECK (weight >= 0);
