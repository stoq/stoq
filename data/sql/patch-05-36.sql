-- Cannot alter types inside transactions :(
commit;
ALTER TYPE stock_transaction_history_type ADD VALUE 'manual-adjust';
ALTER TYPE stock_transaction_history_type ADD VALUE 'update-stock-cost';
ALTER TYPE stock_transaction_history_type ADD VALUE 'sale-return-to-stock';
ALTER TYPE stock_transaction_history_type ADD VALUE 'undo-returned-sale';
begin;


CREATE OR REPLACE FUNCTION validate_stock_item() RETURNS trigger AS $$
DECLARE
    count_ int;
    errmsg text;
BEGIN
    -- Only allow updates that are not touching quantity/stock_cost
    IF (TG_OP = 'UPDATE' AND
        NEW.quantity = OLD.quantity AND
        NEW.stock_cost = OLD.stock_cost) THEN
        RETURN NEW;
    END IF;

    BEGIN
        SELECT COUNT(1) INTO count_ FROM __inserting_sth
            WHERE warning_note = (
                E'I SHOULD ONLY INSERT OR UPDATE DATA ON PRODUCT_STOCK_ITEM BY ' ||
                E'INSERTING A ROW ON STOCK_TRANSACTION_HISTORY, OTHERWISE MY ' ||
                E'DATABASE WILL BECOME INCONSISTENT. I\'M HEREBY WARNED');
    EXCEPTION WHEN undefined_table THEN
        count_ := 0;
    END;

    IF count_ = 0 THEN
        -- Postgresql will give us a syntaxerror if we try to break
        -- the string in the RAISE EXCEPTION statement
        errmsg := ('product_stock_item should not be inserted or have its ' ||
                   'quantity/stock_cost columns updated manually. ' ||
                   'To do that, insert a row on stock_transaction_history');
        RAISE EXCEPTION '%', errmsg;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER validate_stock_item_trigger
    BEFORE INSERT OR UPDATE ON product_stock_item
    FOR EACH ROW
    EXECUTE PROCEDURE validate_stock_item();


-- Update the validate_stock_item trigger defined on patch-05-34
CREATE OR REPLACE FUNCTION upsert_stock_item() RETURNS trigger AS $$
DECLARE
    stock_cost_ numeric(20, 8);
    psi product_stock_item%ROWTYPE;
BEGIN

    CREATE TEMPORARY TABLE __inserting_sth (warning_note text NOT NULL);
    INSERT INTO __inserting_sth (warning_note) VALUES
        (E'I SHOULD ONLY INSERT OR UPDATE DATA ON PRODUCT_STOCK_ITEM BY ' ||
         E'INSERTING A ROW ON STOCK_TRANSACTION_HISTORY, OTHERWISE MY ' ||
         E'DATABASE WILL BECOME INCONSISTENT. I\'M HEREBY WARNED');

    IF NEW.batch_id IS NOT NULL THEN
        SELECT * INTO psi FROM product_stock_item
            WHERE branch_id = NEW.branch_id AND
                  batch_id = NEW.batch_id AND
                  storable_id = NEW.storable_id;
    ELSE
        SELECT * INTO psi FROM product_stock_item
            WHERE branch_id = NEW.branch_id AND
                  storable_id = NEW.storable_id;
    END IF;

    IF FOUND THEN
        IF NEW.type = 'manual-adjust' THEN
            -- Manual adjusts will not alter the quantity of the stock item.
            -- They are used only to adjust any divergence between the sum of the
            -- transactions quantities and the actual quantity on the stock item.
            IF NEW.unit_cost IS NULL THEN
                RAISE EXCEPTION 'unit_cost cannot be NULL on manual-adjust transactions';
            END IF;
            NEW.stock_cost := NEW.unit_cost;
            DROP TABLE __inserting_sth;
            RETURN NEW;
        ELSIF NEW.quantity > 0 AND NEW.unit_cost IS NOT NULL THEN
            -- Only update the cost if increasing the stock and the new unit_cost is provided
            -- Removing an item from stock does not change the stock cost.
            stock_cost_ := (((psi.quantity * psi.stock_cost) + (NEW.quantity * NEW.unit_cost)) /
                            (psi.quantity + NEW.quantity));
        ELSIF NEW.type = 'update-stock-cost' THEN
            IF NEW.quantity != 0 THEN
                RAISE EXCEPTION 'quantity need to be 0 for update-stock-cost transactions';
            END IF;
            stock_cost_ := NEW.unit_cost;
        ELSE
            stock_cost_ := psi.stock_cost;
        END IF;

        NEW.stock_cost := stock_cost_;
        UPDATE product_stock_item SET
                quantity = quantity + NEW.quantity,
                stock_cost = stock_cost_
            WHERE id = psi.id;
    ELSE
        -- Make sure that update-stock-cost only happens for existing
        -- product_stock_items
        IF NEW.type IN ('manual-adjust', 'update-stock-cost') THEN
            RAISE EXCEPTION 'Cannot adjust stock/cost of non-existing product_stock_item';
        END IF;

        -- In this case, this is the first transaction history for this
        -- stock item. There's no stock_cost calculation to do as it will be
        -- equal to the unit_cost itself
        INSERT INTO product_stock_item
                (storable_id, batch_id, branch_id,
                 stock_cost, quantity)
            VALUES
                (NEW.storable_id, NEW.batch_id, NEW.branch_id,
                 COALESCE(NEW.unit_cost, 0), NEW.quantity)
            RETURNING * INTO psi;
        NEW.stock_cost := psi.stock_cost;
    END IF;

    DROP TABLE __inserting_sth;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Disable update_te so those objects won't be marked as dirty
ALTER TABLE stock_transaction_history DISABLE RULE update_te;

UPDATE stock_transaction_history AS sth SET
    batch_id = psi.batch_id,
    branch_id = psi.branch_id,
    storable_id = psi.storable_id,
    type = CASE
        -- Adjust wrong type for sale/wo reserved returning to stock
        WHEN type = 'sale-reserved' and sth.quantity > 0 THEN 'sale-return-to-stock'
        WHEN type = 'wo-used' and sth.quantity > 0 THEN 'wo-returned-to-stock'
        WHEN type = 'returned-sale' and sth.quantity < 0 THEN 'undo-returned-sale'
        ELSE sth.type END,
    unit_cost = CASE
        WHEN type = 'initial' THEN sth.stock_cost
        -- Any other type will be adjusted bellow
        ELSE sth.unit_cost END
FROM product_stock_item psi
WHERE sth.product_stock_item_id = psi.id;

-- Those types don't alter the stock cost on the current code:
-- sell, returned-sale, cancelled-sale, returned-loan, loan,
-- production-allocated, production-produced, production-returned,
-- production-sent, stock-decrease, transfer-to, inventory-adjust, imported,
-- consignment-returned, wo-used, wo-return-to-stock, sale-reserved
UPDATE stock_transaction_history AS sth SET unit_cost = obj.cost
FROM (
    -- received-purchase
    SELECT id, cost as cost FROM receiving_order_item roi UNION
    -- transfer-from
    SELECT id, stock_cost as cost FROM transfer_order_item
) AS obj
WHERE sth.object_id = obj.id;

-- Drop not null from stock_transaction_history so the query bellow works.
-- We will be dropping the column after that.
ALTER TABLE stock_transaction_history ALTER COLUMN product_stock_item_id DROP NOT NULL;

-- Adjust any difference between psi.quantity and sum(sth.quantity)
INSERT INTO stock_transaction_history
    (id, storable_id, batch_id, branch_id, date, quantity, type,
     responsible_id, unit_cost)
SELECT psi.id, psi.storable_id, psi.batch_id, psi.branch_id,
       TRANSACTION_TIMESTAMP(), psi.quantity - SUM(sth.quantity), 'manual-adjust',
       (SELECT id FROM login_user ORDER BY te_id LIMIT 1), psi.stock_cost
     FROM product_stock_item psi
     JOIN stock_transaction_history sth ON sth.product_stock_item_id = psi.id
     GROUP BY psi.id
     HAVING psi.quantity - sum(sth.quantity) != 0;

-- Reenable update_te rule
ALTER TABLE stock_transaction_history ENABLE RULE update_te;

-- Drop product_stock_item_id as it is not necessary anymore and
-- set branch_id/storable_id to not null
ALTER TABLE stock_transaction_history
    DROP COLUMN product_stock_item_id,
    ALTER COLUMN branch_id SET NOT NULL,
    ALTER COLUMN storable_id SET NOT NULL;

-- Create an index on stock_transaction_history to improve performance
-- on queries searching for the candidate key (branch, storable, batch)
CREATE INDEX stock_transaction_history_branch_storable_batch_idx
ON stock_transaction_history (branch_id, storable_id, batch_id);
