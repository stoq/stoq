--
--  Credit Card Transaction details
--

ALTER TABLE credit_card_data
    ADD COLUMN installments integer DEFAULT 1,
    ADD COLUMN entrance_value numeric(10, 2) DEFAULT 0;
