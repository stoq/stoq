ALTER TABLE product ADD COLUMN c_benef TEXT default NULL;
ALTER TABLE product_branch_override ADD COLUMN c_benef TEXT default NULL;

ALTER TABLE invoice_item_icms ADD COLUMN v_icms_deson NUMERIC(20, 2) default NULL;
ALTER TABLE product_icms_template ADD COLUMN mot_des_icms INTEGER;
ALTER TABLE product_icms_template ADD CONSTRAINT valid_mot_des_icms CHECK (mot_des_icms IN (3, 9, 12));
