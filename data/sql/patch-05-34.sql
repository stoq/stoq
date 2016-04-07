ALTER TABLE stock_transaction_history
    ADD COLUMN storable_id uuid REFERENCES storable(id) ON UPDATE CASCADE,
    ADD COLUMN batch_id uuid REFERENCES storable_batch(id) ON UPDATE CASCADE,
    ADD COLUMN branch_id uuid REFERENCES branch(id) ON UPDATE CASCADE,
    ADD COLUMN unit_cost numeric(20, 8);


-- UPDATE stock_transaction_history SET
--     branch_id = i.branch_id,
--     storable_id = i.storable_id,
--     batch_id = i.batch_id
-- FROM product_stock_item i
-- WHERE i.id = stock_transaction_history.product_stock_item_id;


CREATE OR REPLACE FUNCTION upsert_stock_item() RETURNS trigger AS $$
DECLARE
    stock_cost_ numeric(20, 8);
    psi product_stock_item%ROWTYPE;
BEGIN
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
        -- Only update the cost if increasing the stock and the new unit_cost is provided
        -- Removing an item from stock does not change the stock cost.
        -- FIXME: Maybe we need an operation to adjust the stock cost.
        IF NEW.quantity > 0 AND NEW.unit_cost IS NOT NULL THEN
            stock_cost_ := (((psi.quantity * psi.stock_cost) + (NEW.quantity * NEW.unit_cost)) /
                            (psi.quantity + NEW.quantity));
        ELSE
            stock_cost_ := psi.stock_cost;
        END IF;
        UPDATE product_stock_item SET
                quantity = quantity + NEW.quantity,
                stock_cost = stock_cost_
            WHERE id = psi.id;
        NEW.stock_cost := stock_cost_;
    ELSE
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

    NEW.product_stock_item_id := psi.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_stock_item_trigger
    BEFORE INSERT ON stock_transaction_history
    FOR EACH ROW
    EXECUTE PROCEDURE upsert_stock_item();
