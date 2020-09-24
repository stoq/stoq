CREATE OR REPLACE FUNCTION upsert_stock_item() RETURNS trigger AS $$
DECLARE
    stock_cost_ numeric(20, 8);
    stoq_quantity_ numeric(20, 3);
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
            IF psi.quantity = 0 THEN
                stock_cost_ := NEW.unit_cost;
            ELSIF psi.quantity < 0 THEN
                stoq_quantity_ := psi.quantity * -1;
                stock_cost_ := (((stoq_quantity_ * psi.stock_cost) + (NEW.quantity * NEW.unit_cost)) /
                                (stoq_quantity_ + NEW.quantity));
            ELSE
                stock_cost_ := (((psi.quantity * psi.stock_cost) + (NEW.quantity * NEW.unit_cost)) /
                            (psi.quantity + NEW.quantity));
            END IF;
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