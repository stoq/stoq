-- #3795: Redesign Payment methods

-- Financial details is gone
DROP TABLE finance_p_m;
DROP TABLE finance_details;
DELETE FROM apayment_method WHERE child_name = 'FinancePM';

-- PaymentMethod: Add new columns
ALTER TABLE apayment_method ADD COLUMN te_created_id bigint REFERENCES transaction_entry(id);
ALTER TABLE apayment_method ADD COLUMN te_modified_id bigint REFERENCES transaction_entry(id);
ALTER TABLE apayment_method ADD COLUMN method_name text UNIQUE;
ALTER TABLE apayment_method ADD COLUMN description text;
ALTER TABLE apayment_method ADD COLUMN payment_day integer;
ALTER TABLE apayment_method ADD COLUMN closing_day integer;
ALTER TABLE apayment_method ADD COLUMN max_installments integer;
ALTER TABLE apayment_method ADD CONSTRAINT valid_payment_day
        CHECK (payment_day >= 1 AND payment_day <= 28);
ALTER TABLE apayment_method ADD CONSTRAINT valid_closing_day
        CHECK (closing_day >= 1 AND closing_day <= 28);

-- PaymentMethod: Migrate existing fields
UPDATE apayment_method 
   SET te_created_id = inheritable_model.te_created_id,
       te_modified_id = inheritable_model.te_modified_id
  FROM inheritable_model
 WHERE inheritable_model.child_name = 'APaymentMethod' AND
       inheritable_model.id = apayment_method.id;
UPDATE apayment_method SET method_name = 'bill'  WHERE child_name = 'BillPM';
UPDATE apayment_method SET method_name = 'card' WHERE child_name = 'CardPM';
UPDATE apayment_method SET method_name = 'check' WHERE child_name = 'CheckPM';
UPDATE apayment_method SET method_name = 'giftcertificate' WHERE child_name = 'GiftCertificatePM';
UPDATE apayment_method SET method_name = 'money' WHERE child_name = 'MoneyPM';
UPDATE apayment_method 
   SET max_installments = bill_p_m.max_installments_number
  FROM bill_p_m
 WHERE apayment_method.method_name = 'bill';
UPDATE apayment_method 
   SET max_installments = check_p_m.max_installments_number
  FROM check_p_m
 WHERE apayment_method.method_name = 'check';
UPDATE apayment_method SET max_installments = 1 WHERE apayment_method.method_name = 'money';
UPDATE apayment_method SET max_installments = 1 WHERE apayment_method.method_name = 'giftcertificate';
UPDATE apayment_method SET max_installments = 12 WHERE apayment_method.method_name = 'card';

-- PaymentMethod: Drop unused
DELETE FROM inheritable_model WHERE child_name = 'APaymentMethod';
ALTER TABLE apayment_method DROP COLUMN child_name;

-- -- PaymentMethod: Drop unused subclasses
DROP TABLE bill_p_m;
DROP TABLE card_p_m;
DROP TABLE check_p_m;
DROP TABLE gift_certificate_p_m;
DROP TABLE money_p_m;
DROP TABLE payment_method;

ALTER TABLE apayment_method RENAME TO payment_method;
ALTER TABLE apayment_method_id_seq RENAME TO payment_method_id_seq;
ALTER TABLE abstract_payment_group DROP COLUMN default_method;

-- PMDetails & subclasses
ALTER TABLE payment DROP COLUMN method_details_id;

-- This contains nothing useful, shouldn't have
-- been persistent from the start
DROP TABLE bill_check_group_data;

-- These are unused, but we should keep them so we can
-- migrate data from them when we reimplement that
-- functionallity
-- credit_card_details: no fields, just links
-- debit_card_details: receive_days
-- card_installments_provider_details: max_installments_number
-- card_installments_store_details: max_installments_number
-- card_installment_settings: payment_day, closing_day
-- credit_provider_group_data: no fields, just links
-- payment_method_details: commission, provider links
