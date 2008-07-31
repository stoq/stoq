-- #2244: Implementar wizard para cotação de compras

-- Add not null constraint to supplier_id and product_id
ALTER TABLE product_supplier_info
    ALTER COLUMN supplier_id SET NOT NULL,
    ALTER COLUMN product_id SET NOT NULL;
