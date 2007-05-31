-- #3409: Merge AbstractStockItem into ProductStockItem

--
-- 1) Remove InheritableModel inheritence
--

ALTER TABLE abstract_stock_item ADD COLUMN is_valid_model boolean;
ALTER TABLE abstract_stock_item ADD COLUMN te_created_id bigint REFERENCES transaction_entry(id);
ALTER TABLE abstract_stock_item ADD COLUMN te_modified_id bigint REFERENCES transaction_entry(id);
ALTER TABLE abstract_stock_item DROP COLUMN child_name;

UPDATE abstract_stock_item 
   SET te_created_id = inheritable_model.te_created_id,
       te_modified_id = inheritable_model.te_modified_id,
       is_valid_model = inheritable_model.is_valid_model
  FROM inheritable_model
 WHERE inheritable_model.child_name = 'ASellableCategory';
DELETE FROM inheritable_model WHERE child_name = 'ASellableCategory';

--
-- 2) Remove ProductStockItem
--

ALTER TABLE abstract_stock_item ADD COLUMN storable_id bigint 
      REFERENCES product_adapt_to_storable(id);

UPDATE abstract_stock_item 
   SET storable_id = product_stock_item.storable_id 
  FROM product_stock_item 
 WHERE abstract_stock_item.id = product_stock_item.id;

DROP TABLE product_stock_item CASCADE;

--
-- 3) Rename AbstractStockItem to ProductStockItem
--
ALTER TABLE abstract_stock_item RENAME TO product_stock_item;
ALTER TABLE abstract_stock_item_id_seq RENAME TO product_stock_item_id_seq;
