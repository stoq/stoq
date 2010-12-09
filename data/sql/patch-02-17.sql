-- usar 3 casas decimais para quantidade de produtos

-- inventory.py
ALTER TABLE inventory_item ALTER COLUMN actual_quantity TYPE numeric(10, 3);
ALTER TABLE inventory_item ALTER COLUMN recorded_quantity TYPE numeric(10, 3);

-- loan.py
ALTER TABLE loan_item ALTER COLUMN quantity TYPE numeric(10, 3);
ALTER TABLE loan_item ALTER COLUMN sale_quantity TYPE numeric(10, 3);
ALTER TABLE loan_item ALTER COLUMN return_quantity TYPE numeric(10, 3);


-- production.py
ALTER TABLE production_item ALTER COLUMN quantity TYPE numeric(10, 3);
ALTER TABLE production_item ALTER COLUMN produced TYPE numeric(10, 3);
ALTER TABLE production_item ALTER COLUMN lost TYPE numeric(10, 3);

ALTER TABLE production_material ALTER COLUMN needed TYPE numeric(10, 3);
ALTER TABLE production_material ALTER COLUMN allocated TYPE numeric(10, 3);
ALTER TABLE production_material ALTER COLUMN consumed TYPE numeric(10, 3);
ALTER TABLE production_material ALTER COLUMN lost TYPE numeric(10, 3);
ALTER TABLE production_material ALTER COLUMN to_purchase TYPE numeric(10, 3);
ALTER TABLE production_material ALTER COLUMN to_make TYPE numeric(10, 3);

ALTER TABLE production_service ALTER COLUMN quantity TYPE numeric(10, 3);-- Really?

-- product.py
ALTER TABLE product_supplier_info ALTER COLUMN minimum_purchase TYPE numeric(10, 3);
ALTER TABLE product_retention_history ALTER COLUMN quantity TYPE numeric(10, 3);

ALTER TABLE product_history ALTER COLUMN quantity_sold TYPE numeric(10,3);
ALTER TABLE product_history ALTER COLUMN quantity_received TYPE numeric(10,3);
ALTER TABLE product_history ALTER COLUMN quantity_transfered TYPE numeric(10,3);
ALTER TABLE product_history ALTER COLUMN quantity_retained TYPE numeric(10,3);
ALTER TABLE product_history ALTER COLUMN quantity_produced TYPE numeric(10,3);
ALTER TABLE product_history ALTER COLUMN quantity_consumed TYPE numeric(10,3);
ALTER TABLE product_history ALTER COLUMN quantity_lost TYPE numeric(10,3);
ALTER TABLE product_history ALTER COLUMN quantity_decreased TYPE numeric(10,3);

ALTER TABLE product_stock_item ALTER COLUMN quantity TYPE numeric(10,3);
ALTER TABLE product_stock_item ALTER COLUMN logic_quantity TYPE numeric(10,3);

ALTER TABLE product_adapt_to_storable ALTER COLUMN minimum_quantity TYPE numeric(10,3);
ALTER TABLE product_adapt_to_storable ALTER COLUMN maximum_quantity TYPE numeric(10,3);

ALTER TABLE product_component ALTER COLUMN quantity TYPE numeric(10,3);

-- purchase.py
ALTER TABLE purchase_item ALTER COLUMN quantity TYPE numeric(10,3);
ALTER TABLE purchase_item ALTER COLUMN quantity_received TYPE numeric(10,3);
ALTER TABLE purchase_item ALTER COLUMN quantity_sold TYPE numeric(10,3);
ALTER TABLE purchase_item ALTER COLUMN quantity_returned TYPE numeric(10,3);

-- receiving.py
ALTER TABLE receiving_order_item ALTER COLUMN quantity TYPE numeric(10,3);

-- sale.py
ALTER TABLE sale_item ALTER COLUMN quantity TYPE numeric(10, 3);
ALTER TABLE delivery_item ALTER COLUMN quantity TYPE numeric(10, 3);

-- stockdecrease.py
ALTER TABLE stock_decrease_item ALTER COLUMN quantity TYPE numeric(10, 3);

-- transfer.py
ALTER TABLE transfer_order_item ALTER COLUMN quantity TYPE numeric(10, 3);

