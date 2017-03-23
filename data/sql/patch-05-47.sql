--This must be done because we cannot add a new value to a enum into a
--transaction
commit;
ALTER TYPE loan_status ADD VALUE 'cancelled';
ALTER TYPE stock_decrease_status ADD VALUE 'cancelled';
ALTER TYPE stock_transaction_history_type ADD VALUE 'cancelled-transfer';
ALTER TYPE stock_transaction_history_type ADD VALUE 'cancelled-loan';
ALTER TYPE stock_transaction_history_type ADD VALUE 'cancelled-stock-decrease';
ALTER TYPE stock_transaction_history_type ADD VALUE 'cancelled-inventory-adjust';
begin;

--Add cancel_reason column
ALTER TABLE inventory ADD cancel_reason TEXT;
ALTER TABLE loan ADD cancel_reason TEXT;
ALTER TABLE sale ADD cancel_reason TEXT;
ALTER TABLE stock_decrease ADD cancel_reason TEXT;
ALTER TABLE transfer_order ADD cancel_reason TEXT;

--Add cancel_date column
ALTER TABLE inventory ADD cancel_date TIMESTAMP;
ALTER TABLE loan ADD cancel_date TIMESTAMP;
ALTER TABLE stock_decrease ADD cancel_date TIMESTAMP;

--Add cancel_responsible_id column
ALTER TABLE inventory ADD cancel_responsible_id UUID REFERENCES login_user(id)
    ON UPDATE CASCADE;
ALTER TABLE loan ADD cancel_responsible_id UUID REFERENCES login_user(id)
    ON UPDATE CASCADE;
ALTER TABLE sale ADD cancel_responsible_id UUID REFERENCES login_user(id)
    ON UPDATE CASCADE;
ALTER TABLE stock_decrease ADD cancel_responsible_id UUID
    REFERENCES login_user(id) ON UPDATE CASCADE;

--Move sale cancellation note from sale_comment to the new column cancel_reason
UPDATE sale SET cancel_reason = subquery.comment,
    cancel_responsible_id = subquery.author_id FROM (
    SELECT comment, author_id, sale_id FROM sale, sale_comment WHERE
        sale.id = sale_comment.sale_id AND sale.status = 'cancelled'
        ORDER BY date DESC LIMIT 1)
    AS subquery WHERE sale.id = subquery.sale_id;
