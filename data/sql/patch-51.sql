-- #3391: Remove BankDestination

--
-- 1) Remove InheritableModel inheritence
--

ALTER TABLE payment_destination ADD COLUMN te_created_id bigint REFERENCES transaction_entry(id);
ALTER TABLE payment_destination ADD COLUMN te_modified_id bigint REFERENCES transaction_entry(id);
ALTER TABLE payment_destination DROP COLUMN child_name;

UPDATE payment_destination 
   SET te_created_id = inheritable_model.te_created_id,
       te_modified_id = inheritable_model.te_modified_id
  FROM inheritable_model
 WHERE inheritable_model.child_name = 'PaymentDestination' AND
       inheritable_model.id = payment_destination.id;;
DELETE FROM inheritable_model WHERE child_name = 'PaymentDestination';

--
-- 2) Migrate branch_id from store_destination to payment_destination
--

ALTER TABLE payment_destination ADD COLUMN branch_id bigint REFERENCES person_adapt_to_branch(id);
UPDATE payment_destination 
   SET branch_id = store_destination.branch_id 
  FROM store_destination
 WHERE payment_destination.branch_id = store_destination.branch_id;

--
-- 3) Drop BankDestination and StoreDestination tables
--
DROP TABLE bank_destination;
DROP TABLE store_destination;
