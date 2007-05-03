-- #3338: Ao tentar utilizar o tipo de frete como FOB um erro é gerado
ALTER TABLE purchase_order
    DROP CONSTRAINT valid_freight_type,
    ADD CONSTRAINT valid_freight_type
        CHECK (freight_type >= 0 AND freight_type < 2);
