-- #3297: Remove ReceivingOrder IPaymentGroup implementation
DELETE FROM abstract_fiscal_book_entry WHERE id IN (
  SELECT abstract_fiscal_book_entry.id
   FROM abstract_fiscal_book_entry, abstract_payment_group
  WHERE payment_group_id = abstract_payment_group.id AND
        abstract_payment_group.child_name = 'ReceivingOrderAdaptToPaymentGroup');
DELETE FROM abstract_payment_group where child_name = 'ReceivingOrderAdaptToPaymentGroup';
DELETE from receiving_order WHERE purchase_id IS NULL;
ALTER TABLE receiving_order ALTER COLUMN purchase_id SET NOT NULL;
DROP TABLE receiving_order_adapt_to_payment_group;
