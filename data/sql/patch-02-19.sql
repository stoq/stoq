-- Creation of taxes tables


--
--  Product Template Classes
--

ALTER TABLE product_icms_template
    ADD COLUMN csosn integer,
    ADD COLUMN p_cred_sn numeric(10,2);


--
--  Sale Item Classes
--

ALTER TABLE sale_item_icms
    ADD COLUMN csosn integer,
    ADD COLUMN p_cred_sn numeric(10,2),
    ADD COLUMN v_cred_icms_sn numeric(10,2),
    ADD COLUMN v_bc_st_ret numeric(10,2),
    ADD COLUMN v_icms_st_ret numeric(10,2);


