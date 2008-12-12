-- #3708: Incluir ao sintegra a geração do registro 74, relativo a inventário

-- We need to include the cost of the product when we close the inventory
ALTER TABLE inventory_item
    ADD COLUMN product_cost numeric(10, 2)
    CONSTRAINT positive_product_cost CHECK (product_cost >= 0);
