-- #3488: ASellableItem should be SaleItem and avoid InheritableModel

--
-- 1) Remove InheritableModel inheritence
--

ALTER TABLE asellable_item ADD COLUMN te_created_id bigint REFERENCES transaction_entry(id);
ALTER TABLE asellable_item ADD COLUMN te_modified_id bigint REFERENCES transaction_entry(id);

UPDATE asellable_item
   SET te_created_id = inheritable_model.te_created_id,
       te_modified_id = inheritable_model.te_modified_id
  FROM inheritable_model
 WHERE inheritable_model.child_name = 'ASellableItem';
DELETE FROM inheritable_model WHERE child_name = 'ASellableItem';
       
--
-- 2) Remove ProductSellableItem, ServiceSellableItem, GiftCertificateItem,
--    ProductStockReference
--

ALTER TABLE asellable_item ADD COLUMN notes TEXT;
ALTER TABLE asellable_item ADD COLUMN estimated_fix_date timestamp;
ALTER TABLE asellable_item ADD COLUMN completion_date timestamp;

ALTER TABLE service_sellable_item_adapt_to_delivery DROP COLUMN original_id;

UPDATE asellable_item 
   SET notes = service_sellable_item.notes,
       estimated_fix_date = service_sellable_item.estimated_fix_date,
       completion_date = service_sellable_item.completion_date
  FROM service_sellable_item
 WHERE asellable_item.id = service_sellable_item.id;
DROP TABLE service_sellable_item;

DROP TABLE product_stock_reference;
DROP TABLE product_sellable_item;
DROP TABLE gift_certificate_item;

--
-- 3) Rename ASellableItem to SaleItem
--
ALTER TABLE asellable_item DROP COLUMN child_name;
ALTER TABLE asellable_item RENAME TO sale_item;
ALTER TABLE asellable_item_id_seq RENAME TO sale_item_id_seq;

ALTER TABLE service_sellable_item_adapt_to_delivery ADD COLUMN original_id bigint REFERENCES sale_item(id);
ALTER TABLE service_sellable_item_adapt_to_delivery RENAME TO sale_item_adapt_to_delivery;
ALTER TABLE service_sellable_item_adapt_to_delivery_id_seq RENAME TO sale_item_adapt_to_delivery_id_seq;
