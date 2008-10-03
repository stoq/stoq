-- #3519: Refactor Payment Groups
ALTER TABLE abstract_payment_group DROP COLUMN open_date;
ALTER TABLE abstract_payment_group DROP COLUMN close_date;
ALTER TABLE abstract_payment_group DROP COLUMN cancel_date;
ALTER TABLE abstract_payment_group DROP COLUMN installments_number;
ALTER TABLE abstract_payment_group DROP COLUMN interval_type;
ALTER TABLE abstract_payment_group DROP COLUMN intervals;
ALTER TABLE abstract_payment_group ADD COLUMN payer_id bigint REFERENCES person(id);
ALTER TABLE abstract_payment_group ADD COLUMN recipient_id bigint REFERENCES person(id);

ALTER TABLE sale ADD COLUMN group_id bigint REFERENCES abstract_payment_group(id);
ALTER TABLE purchase_order ADD COLUMN group_id bigint REFERENCES abstract_payment_group(id);

UPDATE sale
   SET group_id = abstract_payment_group.id
  FROM abstract_payment_group, sale_adapt_to_payment_group
 WHERE sale_adapt_to_payment_group.original_id = sale.id AND
       abstract_payment_group.id = sale_adapt_to_payment_group.id;
UPDATE purchase_order
   SET group_id = abstract_payment_group.id
  FROM abstract_payment_group, purchase_order_adapt_to_payment_group
 WHERE purchase_order_adapt_to_payment_group.original_id = purchase_order.id AND
       abstract_payment_group.id = purchase_order_adapt_to_payment_group.id;
DELETE FROM inheritable_model_adapter WHERE child_name = 'AbstractPaymentGroup';
SELECT setval('abstract_payment_group_id_seq', (SELECT last_value from inheritable_model_adapter_id_seq));

ALTER TABLE abstract_payment_group RENAME TO payment_group;
ALTER TABLE abstract_payment_group_id_seq RENAME TO payment_group_id_seq;

ALTER TABLE payment_group DROP COLUMN child_name;
DROP TABLE sale_adapt_to_payment_group;
DROP TABLE purchase_order_adapt_to_payment_group;

