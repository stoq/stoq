-- #3052: Implementar opção de alteracao da data de vencimento Contas a
-- Receber.

-- rename payment_due_date_info, now that it will hold more information, and
-- add columns to store old and new statuses
ALTER TABLE payment_due_date_info RENAME TO payment_change_history;
ALTER TABLE payment_due_date_info_id_seq RENAME TO payment_change_history_id_seq;

ALTER TABLE payment_change_history DROP COLUMN responsible_id;

ALTER TABLE payment_change_history
    RENAME COLUMN due_date_change_reason TO change_reason;

ALTER TABLE payment_change_history ADD COLUMN new_due_date timestamp;
ALTER TABLE payment_change_history ADD COLUMN last_status integer;
ALTER TABLE payment_change_history ADD COLUMN new_status integer;
