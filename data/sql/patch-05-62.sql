ALTER TABLE receiving_order_item
    ADD ipi_value NUMERIC(20, 2) CONSTRAINT positive_ipi CHECK (ipi_value >= 0),
    ADD icms_st_value NUMERIC(20, 2) CONSTRAINT positive_icms_st CHECK (icms_st_value >= 0);

ALTER TABLE purchase_item
    ADD ipi_value NUMERIC(20, 2) CONSTRAINT positive_ipi CHECK (ipi_value >= 0),
    ADD icms_st_value NUMERIC(20, 2) CONSTRAINT positive_icms_st CHECK (icms_st_value >= 0);
