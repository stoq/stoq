-- #3071: Implementar Interface para consulta de comissões.

-- Add column total_amount in sale table
ALTER TABLE sale ADD COLUMN total_amount numeric(10, 2) NOT NULL
    CONSTRAINT positive_total_amount CHECK (total_amount >= 0);

UPDATE sale
    SET total_amount = (
        SELECT SUM(sale_item.quantity * sale_item.price)
                - discount_value + surcharge_value
        FROM sale_item
        WHERE sale.id = sale_item.sale_id
GROUP BY discount_value, surcharge_value);
