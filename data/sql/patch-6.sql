-- #3301: Refactor SellableCategory

--
-- 1) Remove InheritableModel inheritence
--

ALTER TABLE asellable_category ADD COLUMN is_valid_model boolean;
ALTER TABLE asellable_category ADD COLUMN te_created_id bigint REFERENCES transaction_entry(id);
ALTER TABLE asellable_category ADD COLUMN te_modified_id bigint REFERENCES transaction_entry(id);
ALTER TABLE asellable_category DROP COLUMN child_name;

UPDATE asellable_category 
   SET te_created_id = inheritable_model.te_created_id,
       te_modified_id = inheritable_model.te_modified_id,
       is_valid_model = inheritable_model.is_valid_model
  FROM inheritable_model
 WHERE inheritable_model.child_name = 'ASellableCategory';
DELETE FROM inheritable_model WHERE child_name = 'ASellableCategory';

--
-- 2) Remove SellableCategory & BaseSellableCategory
--

-- Migrate base_category_id from sellable_category to asellable_category
ALTER TABLE asellable_category ADD COLUMN category_id bigint REFERENCES asellable_category(id);
UPDATE asellable_category 
   SET category_id = sellable_category.base_category_id 
  FROM sellable_category 
 WHERE asellable_category.id = sellable_category.id;

-- Point to ASellableCategory instead of SellableCategory
ALTER TABLE asellable DROP CONSTRAINT asellable_category_id_fkey;
ALTER TABLE asellable ADD CONSTRAINT asellable_category_id_fkey FOREIGN KEY (category_id) REFERENCES asellable_category(id);

-- Drop SellableCategory and BaseSellableCategory tables
DROP TABLE sellable_category;
DROP TABLE base_sellable_category;

--
-- 3) Rename to SellableCategory
--
ALTER TABLE asellable_category RENAME TO sellable_category;
ALTER TABLE asellable_category_id_seq RENAME TO sellable_category_id_seq;
