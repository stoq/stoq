-- Add production history (produced, consumed and lost items) in product history.

ALTER TABLE product_history
    ADD COLUMN production_date timestamp,
    ADD COLUMN quantity_consumed numeric(10,2)
        CONSTRAINT positive_consumed CHECK (quantity_consumed > 0),
    ADD COLUMN quantity_produced numeric(10,2)
        CONSTRAINT positive_produced CHECK (quantity_produced > 0),
    ADD COLUMN quantity_lost numeric(10, 2)
        CONSTRAINT positive_lost CHECK (quantity_lost > 0);
