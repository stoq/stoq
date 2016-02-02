-- Adding column for the request number of a manufacturer in a work order.

ALTER TABLE work_order ADD COLUMN supplier_order text;
