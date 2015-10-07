-- Make product, service and storable use the same id as sellable

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
