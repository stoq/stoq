-- #3535: Pesquisa de Histórico de produtos deve apresentar apenas
-- produtos por branch

-- Add quantity_transfered and quantity_retended columns in
-- product_history table

ALTER TABLE product_history
    ADD COLUMN quantity_transfered numeric(10,2)
        CONSTRAINT positive_quantity_transfered CHECK (quantity_transfered >= 0),
    ADD COLUMN quantity_retended numeric(10,2)
        CONSTRAINT positive_quantity_retended CHECK (quantity_retended >= 0);

-- Add status column in transfer_order table

ALTER TABLE transfer_order
    ADD COLUMN status integer CONSTRAINT valid_status CHECK (status >= 0 AND status < 2);
