-- #2897: ProductAdaptToStorable fails when marked as UNIQUE
ALTER TABLE product_adapt_to_storable ADD CONSTRAINT product_adapt_to_storable_original_id_key UNIQUE (original_id);
