-- Make product, service and storable use the same id as sellable

-- Disable update_te for this patch as it is going to be applied to all
-- databases, and all databases will have the same final result
CREATE OR REPLACE FUNCTION update_te(te_id bigint) RETURNS void AS $$
BEGIN
        --UPDATE transaction_entry SET te_time = STATEMENT_TIMESTAMP(), dirty = true WHERE id = $1;
END;
$$ LANGUAGE plpgsql;

-- TODO: We should provide a way for plugins to execute "pre-migration"
-- actions, like this one. Without it this patch would fail for people
-- using the magento plugin.
DROP RULE IF EXISTS magento_on_update ON product;
DROP RULE IF EXISTS magento_on_update ON service;
DROP RULE IF EXISTS magento_on_update ON storable;
DROP RULE IF EXISTS magento_on_update ON product_stock_item;
DROP RULE IF EXISTS magento_on_insert ON product_stock_item;

UPDATE parameter_data SET field_value = service.sellable_id::text
  FROM service
  WHERE parameter_data.field_name = 'DELIVERY_SERVICE' AND
        parameter_data.field_value = service.id::text;

UPDATE service SET id = sellable_id;
ALTER TABLE service
    DROP COLUMN sellable_id,
    DROP CONSTRAINT IF EXISTS "service_sellable_id_fkey",
    ADD CONSTRAINT "service_id_fkey" FOREIGN KEY (id) REFERENCES sellable(id) ON UPDATE CASCADE;

UPDATE storable SET id = product.sellable_id FROM product
    WHERE product.id = storable.product_id;
ALTER TABLE storable
    DROP COLUMN product_id,
    DROP CONSTRAINT IF EXISTS "storable_product_id_fkey";

UPDATE product SET id = sellable_id;
ALTER TABLE product
    DROP COLUMN sellable_id,
    DROP CONSTRAINT IF EXISTS "product_sellable_id_fkey",
    ADD CONSTRAINT "product_id_fkey" FOREIGN KEY (id) REFERENCES sellable(id) ON UPDATE CASCADE;

ALTER TABLE storable
    ADD CONSTRAINT "storable_id_fkey" FOREIGN KEY (id) REFERENCES product(id) ON UPDATE CASCADE;

-- Recreate the trigger
CREATE OR REPLACE FUNCTION update_te(te_id bigint) RETURNS void AS $$
BEGIN
        UPDATE transaction_entry SET te_time = STATEMENT_TIMESTAMP(), dirty = true WHERE id = $1;
END;
$$ LANGUAGE plpgsql;
