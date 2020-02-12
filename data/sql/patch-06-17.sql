-- Add category_id column
ALTER TABLE image
ADD COLUMN category_id uuid REFERENCES sellable_category(id) ON UPDATE CASCADE,
ADD CONSTRAINT check_exist_one_image
    CHECK (((category_id IS NOT NULL) AND (sellable_id IS NULL)) OR
          ((category_id IS NULL) AND (sellable_id IS NOT NULL)) OR
          ((category_id IS NULL) AND (sellable_id IS NULL)));