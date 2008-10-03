-- #2244: Implementar wizard para cotação de compras

-- Assert that we don't have null values before we add the constraint
DELETE FROM product_supplier_info WHERE product_id IS NULL OR  supplier_id IS NULL;

-- Add not null constraint to supplier_id and product_id
ALTER TABLE product_supplier_info
    ALTER COLUMN supplier_id SET NOT NULL,
    ALTER COLUMN product_id SET NOT NULL;
