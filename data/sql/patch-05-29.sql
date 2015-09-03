-- REMOVING UNUSED COLUMNS.
ALTER TABLE product_pis_template DROP COLUMN v_bc,
                                 DROP COLUMN v_aliq_prod,
                                 DROP COLUMN q_bc_prod;

ALTER TABLE product_cofins_template DROP COLUMN v_bc,
                                    DROP COLUMN v_aliq_prod,
                                    DROP COLUMN q_bc_prod;

ALTER TABLE invoice_item_pis DROP COLUMN product_tax_template_id,
                             DROP COLUMN v_aliq_prod;

ALTER TABLE invoice_item_cofins DROP COLUMN product_tax_template_id,
                                DROP COLUMN v_aliq_prod;

-- PRODUCT
-- Insert columns of tax identity.
ALTER TABLE product ADD COLUMN pis_template_id uuid DEFAULT NULL;
ALTER TABLE product ADD CONSTRAINT product_pis_template_id_fkey
    FOREIGN KEY (pis_template_id) REFERENCES product_pis_template (id) ON UPDATE CASCADE;

UPDATE product SET pis_template_id = product_pis_template.id
    FROM product_pis_template
    WHERE product.pis_template_id = product_pis_template.id;

ALTER TABLE product ADD COLUMN cofins_template_id uuid DEFAULT NULL;
ALTER TABLE product ADD CONSTRAINT product_cofins_template_id_fkey
    FOREIGN KEY (cofins_template_id) REFERENCES product_cofins_template (id) ON UPDATE CASCADE;

UPDATE product SET cofins_template_id = product_cofins_template.id
    FROM product_cofins_template
    WHERE product.cofins_template_id = product_cofins_template.id;

-- SALE_ITEM
-- Insert columns of tax identity.
ALTER TABLE sale_item ADD COLUMN pis_info_id uuid DEFAULT NULL;
ALTER TABLE sale_item ADD CONSTRAINT sale_item_pis_info_id_fkey
    FOREIGN KEY (pis_info_id) REFERENCES invoice_item_pis (id) ON UPDATE CASCADE;

UPDATE sale_item SET pis_info_id = invoice_item_pis.id
    FROM invoice_item_pis
    WHERE sale_item.pis_info_id = invoice_item_pis.id;

ALTER TABLE sale_item ADD COLUMN cofins_info_id uuid DEFAULT NULL;
ALTER TABLE sale_item ADD CONSTRAINT sale_item_cofins_info_id_fkey
    FOREIGN KEY (cofins_info_id) REFERENCES invoice_item_cofins (id) ON UPDATE CASCADE;

UPDATE sale_item SET cofins_info_id = invoice_item_cofins.id
    FROM invoice_item_cofins
    WHERE sale_item.cofins_info_id = invoice_item_cofins.id;

-- STOCK_DECREASE_ITEM
-- Insert columns of tax identity.
ALTER TABLE stock_decrease_item ADD COLUMN pis_info_id uuid DEFAULT NULL;
ALTER TABLE stock_decrease_item ADD CONSTRAINT stock_decrease_item_pis_info_id_fkey
    FOREIGN KEY (pis_info_id) REFERENCES invoice_item_pis (id) ON UPDATE CASCADE;

UPDATE stock_decrease_item SET pis_info_id = invoice_item_pis.id
    FROM invoice_item_pis
    WHERE stock_decrease_item.pis_info_id = invoice_item_pis.id;

ALTER TABLE stock_decrease_item ADD COLUMN cofins_info_id uuid DEFAULT NULL;
ALTER TABLE stock_decrease_item ADD CONSTRAINT stock_decrease_item_cofins_info_id_fkey
    FOREIGN KEY (cofins_info_id) REFERENCES invoice_item_cofins (id) ON UPDATE CASCADE;

UPDATE stock_decrease_item SET cofins_info_id = invoice_item_cofins.id
    FROM invoice_item_cofins
    WHERE stock_decrease_item.cofins_info_id = invoice_item_cofins.id;

-- TRANSFER_ORDER_ITEM
-- Insert columns of tax identity.
ALTER TABLE transfer_order_item ADD COLUMN pis_info_id uuid DEFAULT NULL;
ALTER TABLE transfer_order_item ADD CONSTRAINT transfer_order_item_pis_info_id_fkey
    FOREIGN KEY (pis_info_id) REFERENCES invoice_item_pis (id) ON UPDATE CASCADE;

UPDATE transfer_order_item SET pis_info_id = invoice_item_pis.id
    FROM invoice_item_pis
    WHERE transfer_order_item.pis_info_id = invoice_item_pis.id;

ALTER TABLE transfer_order_item ADD COLUMN cofins_info_id uuid DEFAULT NULL;
ALTER TABLE transfer_order_item ADD CONSTRAINT transfer_order_item_cofins_info_id_fkey
    FOREIGN KEY (cofins_info_id) REFERENCES invoice_item_cofins (id) ON UPDATE CASCADE;

UPDATE transfer_order_item SET cofins_info_id = invoice_item_cofins.id
    FROM invoice_item_cofins
    WHERE transfer_order_item.cofins_info_id = invoice_item_cofins.id;

-- RETURNED_SALE_ITEM
-- Insert columns of tax identity.
ALTER TABLE returned_sale_item ADD COLUMN pis_info_id uuid DEFAULT NULL;
ALTER TABLE returned_sale_item ADD CONSTRAINT returned_sale_item_pis_info_id_fkey
    FOREIGN KEY (pis_info_id) REFERENCES invoice_item_pis (id) ON UPDATE CASCADE;

UPDATE returned_sale_item SET pis_info_id = invoice_item_pis.id
    FROM invoice_item_pis
    WHERE returned_sale_item.pis_info_id = invoice_item_pis.id;

ALTER TABLE returned_sale_item ADD COLUMN cofins_info_id uuid DEFAULT NULL;
ALTER TABLE returned_sale_item ADD CONSTRAINT returned_sale_item_cofins_info_id_fkey
    FOREIGN KEY (cofins_info_id) REFERENCES invoice_item_cofins (id) ON UPDATE CASCADE;

UPDATE returned_sale_item SET cofins_info_id = invoice_item_cofins.id
    FROM invoice_item_cofins
    WHERE returned_sale_item.cofins_info_id = invoice_item_cofins.id;
