ALTER TABLE product_icms_template
    ADD COLUMN p_fcp NUMERIC(10, 2),
    ADD COLUMN p_fcp_st NUMERIC(10, 2);

ALTER TABLE invoice_item_icms
    ADD COLUMN p_fcp NUMERIC(10, 2),
    ADD COLUMN p_fcp_st NUMERIC(10, 2),
    ADD COLUMN p_st NUMERIC(10, 2),
    ADD COLUMN v_fcp NUMERIC(20, 2),
    ADD COLUMN v_fcp_st NUMERIC(20, 2),
    ADD COLUMN v_fcp_st_ret NUMERIC(20, 2);

