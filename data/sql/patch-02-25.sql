--
--  #4324: Calculo do Imposto CSOSN 101
--  Add p_cred_sn_valid_until column on product_icms_template table.
--

ALTER TABLE product_icms_template
    ADD COLUMN p_cred_sn_valid_until timestamp DEFAULT NULL;

