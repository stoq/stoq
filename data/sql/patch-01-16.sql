-- #3068: Implementar função de "estoque de segurança" ou "estoque mínimo".

ALTER TABLE product_adapt_to_storable
    ADD COLUMN minimum_quantity numeric(10, 2) DEFAULT 0
        CONSTRAINT positive_minimum_quantity CHECK (minimum_quantity >= 0),
    ADD COLUMN maximum_quantity numeric(10, 2) DEFAULT 0
        CONSTRAINT positive_maximum_quantity CHECK (maximum_quantity >= 0);
