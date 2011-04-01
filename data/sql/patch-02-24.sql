--
--  Credit Card Transaction details
--

ALTER TABLE credit_card_data
    ADD COLUMN nsu integer DEFAULT NULL;
ALTER TABLE credit_card_data
    ADD COLUMN auth integer DEFAULT NULL;

