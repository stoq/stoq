-- #3811: Get rid persistent sellable adapters
ALTER TABLE product ADD COLUMN sellable_id bigint REFERENCES asellable(id);
ALTER TABLE service ADD COLUMN sellable_id bigint REFERENCES asellable(id);

ALTER TABLE asellable ADD COLUMN te_created_id bigint REFERENCES transaction_entry(id);
ALTER TABLE asellable ADD COLUMN te_modified_id bigint REFERENCES transaction_entry(id);

UPDATE product 
   SET sellable_id = product_adapt_to_sellable.id
  FROM product_adapt_to_sellable
 WHERE product_adapt_to_sellable.original_id = product.id;
DELETE FROM inheritable_model_adapter WHERE child_name = 'ProductAdaptToSellable';
UPDATE service 
   SET sellable_id = service_adapt_to_sellable.id
  FROM service_adapt_to_sellable
 WHERE service_adapt_to_sellable.original_id = service.id;
DELETE FROM inheritable_model_adapter WHERE child_name = 'ServiceAdaptToSellable';
UPDATE asellable
   SET te_created_id = inheritable_model_adapter.te_created_id,
       te_modified_id = inheritable_model_adapter.te_modified_id
  FROM inheritable_model_adapter
 WHERE inheritable_model_adapter.child_name = 'ASellable' AND
       inheritable_model_adapter.id = asellable.id;
SELECT setval('asellable_id_seq', (SELECT last_value from inheritable_model_adapter_id_seq));

ALTER TABLE asellable DROP COLUMN child_name;
DROP TABLE product_adapt_to_sellable;
DROP TABLE service_adapt_to_sellable;

ALTER TABLE asellable RENAME TO sellable;
ALTER TABLE asellable_id_seq RENAME TO sellable_id_seq;

