-- Add year column in product_adapt_to_book table.

ALTER TABLE product_adapt_to_book
    ADD COLUMN year integer DEFAULT 0 CONSTRAINT positive_year CHECK (year >= 0);
