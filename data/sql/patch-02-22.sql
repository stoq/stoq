--
--  Add freight_type column on ReceivingOrder
--

ALTER TABLE receiving_order
    ADD COLUMN freight_type integer DEFAULT 0;

