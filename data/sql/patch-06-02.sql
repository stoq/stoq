ALTER TABLE branch_station ADD COLUMN code text DEFAULT '';
ALTER TABLE credit_card_data
    ALTER auth TYPE text,
    ALTER nsu TYPE text;

-- Make till identifiable
ALTER TABLE till
    ADD COLUMN identifier SERIAL NOT NULL,
    ADD COLUMN branch_id uuid REFERENCES branch(id) ON UPDATE CASCADE;
UPDATE till SET branch_id = branch_station.branch_id
    FROM branch_station WHERE till.station_id = branch_station.id;
ALTER TABLE till ALTER branch_id SET NOT NULL;

-- Add station_id columns
ALTER TABLE inventory ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE loan ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE payment ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE payment_renegotiation ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE production_order ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE purchase_order ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE quotation ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE quote_group ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE receiving_invoice ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE receiving_order ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE returned_sale ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE sale ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE stock_decrease ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE till_entry ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE transfer_order ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;
ALTER TABLE work_order ADD COLUMN station_id uuid REFERENCES branch_station(id) ON UPDATE CASCADE;

-- For (some) sales we can kind of figure out a station for it.
UPDATE sale SET station_id = foo.station_id
    FROM (SELECT DISTINCT sale.id as sale_id, till.station_id FROM till
            JOIN till_entry ON till.id = till_entry.till_id
            JOIN payment ON till_entry.payment_id = payment.id
            JOIN payment_group ON payment_group.id = payment.group_id
            JOIN sale on sale.group_id = payment_group.id) as foo
    WHERE foo.sale_id = sale.id;


-- Others will default to the last branch_station that had a till openened (or any branch_station if
-- that branch have never had a till open - thats the left join)
UPDATE sale SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE sale.station_id IS NULL AND foo.branch_id = sale.branch_id AND foo.rank = 1;
UPDATE sale SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE sale DROP CONSTRAINT sale_identifier_branch_id_key;
ALTER TABLE sale ADD UNIQUE (identifier, branch_id, station_id);

UPDATE inventory SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE inventory.station_id IS NULL AND foo.branch_id = inventory.branch_id AND foo.rank = 1;
UPDATE inventory SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE inventory DROP CONSTRAINT inventory_identifier_branch_id_key;
ALTER TABLE inventory ADD UNIQUE (identifier, branch_id, station_id);

UPDATE loan SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE loan.station_id IS NULL AND foo.branch_id = loan.branch_id AND foo.rank = 1;
UPDATE loan SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE loan DROP CONSTRAINT loan_identifier_branch_id_key;
ALTER TABLE loan ADD UNIQUE (identifier, branch_id, station_id);

UPDATE payment SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE payment.station_id IS NULL AND foo.branch_id = payment.branch_id AND foo.rank = 1;
UPDATE payment SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE payment DROP CONSTRAINT payment_identifier_branch_id_key;
ALTER TABLE payment ADD UNIQUE (identifier, branch_id, station_id);

UPDATE payment_renegotiation SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE payment_renegotiation.station_id IS NULL AND foo.branch_id = payment_renegotiation.branch_id AND foo.rank = 1;
UPDATE payment_renegotiation SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE payment_renegotiation DROP CONSTRAINT payment_renegotiation_identifier_branch_id_key;
ALTER TABLE payment_renegotiation ADD UNIQUE (identifier, branch_id, station_id);

UPDATE production_order SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE production_order.station_id IS NULL AND foo.branch_id = production_order.branch_id AND foo.rank = 1;
UPDATE production_order SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE production_order DROP CONSTRAINT production_order_identifier_branch_id_key;
ALTER TABLE production_order ADD UNIQUE (identifier, branch_id, station_id);

UPDATE purchase_order SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE purchase_order.station_id IS NULL AND foo.branch_id = purchase_order.branch_id AND foo.rank = 1;
UPDATE purchase_order SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE purchase_order DROP CONSTRAINT purchase_order_identifier_branch_id_key;
ALTER TABLE purchase_order ADD UNIQUE (identifier, branch_id, station_id);

UPDATE quotation SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE quotation.station_id IS NULL AND foo.branch_id = quotation.branch_id AND foo.rank = 1;
UPDATE quotation SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE quotation DROP CONSTRAINT quotation_identifier_branch_id_key;
ALTER TABLE quotation ADD UNIQUE (identifier, branch_id, station_id);

UPDATE quote_group SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE quote_group.station_id IS NULL AND foo.branch_id = quote_group.branch_id AND foo.rank = 1;
UPDATE quote_group SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE quote_group DROP CONSTRAINT quote_group_identifier_branch_id_key;
ALTER TABLE quote_group ADD UNIQUE (identifier, branch_id, station_id);

UPDATE receiving_order SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE receiving_order.station_id IS NULL AND foo.branch_id = receiving_order.branch_id AND foo.rank = 1;
UPDATE receiving_order SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE receiving_order DROP CONSTRAINT receiving_order_identifier_branch_id_key;
ALTER TABLE receiving_order ADD UNIQUE (identifier, branch_id, station_id);


UPDATE receiving_invoice SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE receiving_invoice.station_id IS NULL AND foo.branch_id = receiving_invoice.branch_id AND foo.rank = 1;
UPDATE receiving_invoice SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;

-- There may be some receiving_invoice without a branch!
UPDATE receiving_invoice SET station_id = receiving_order.station_id
    FROM receiving_order
    WHERE receiving_order.receiving_invoice_id = receiving_invoice.id AND receiving_invoice.station_id IS NULL;

-- While we are at it, add a not null to receiving_invoice.branch_id
UPDATE receiving_invoice SET branch_id = receiving_order.branch_id
    FROM receiving_order
    WHERE receiving_order.receiving_invoice_id = receiving_invoice.id AND receiving_invoice.branch_id IS NULL;
ALTER TABLE receiving_invoice ALTER branch_id SET NOT NULL;


-- This table never got this unique key
-- ALTER TABLE receiving_invoice DROP CONSTRAINT receiving_invoice_identifier_branch_id_key;
ALTER TABLE receiving_invoice ADD UNIQUE (identifier, branch_id, station_id);

UPDATE returned_sale SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE returned_sale.station_id IS NULL AND foo.branch_id = returned_sale.branch_id AND foo.rank = 1;
UPDATE returned_sale SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE returned_sale DROP CONSTRAINT returned_sale_identifier_branch_id_key;
ALTER TABLE returned_sale ADD UNIQUE (identifier, branch_id, station_id);

UPDATE stock_decrease SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE stock_decrease.station_id IS NULL AND foo.branch_id = stock_decrease.branch_id AND foo.rank = 1;
UPDATE stock_decrease SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE stock_decrease DROP CONSTRAINT stock_decrease_identifier_branch_id_key;
ALTER TABLE stock_decrease ADD UNIQUE (identifier, branch_id, station_id);

UPDATE work_order SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE work_order.station_id IS NULL AND foo.branch_id = work_order.branch_id AND foo.rank = 1;
UPDATE work_order SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE work_order DROP CONSTRAINT work_order_identifier_branch_id_key;
ALTER TABLE work_order ADD UNIQUE (identifier, branch_id, station_id);

UPDATE transfer_order SET station_id = foo.id
    FROM (SELECT branch_station.id, branch_station.branch_id, rank() OVER (partition by branch_station.branch_id order by opening_date desc)
        FROM branch_station LEFT JOIN till ON branch_station.id = till.station_id) as foo
    WHERE transfer_order.station_id IS NULL AND foo.branch_id = transfer_order.source_branch_id AND foo.rank = 1;
UPDATE transfer_order SET station_id = foo.id FROM (SELECT id FROM branch_station ORDER BY te_id LIMIT 1) as foo WHERE station_id IS NULL;
ALTER TABLE transfer_order DROP CONSTRAINT transfer_order_identifier_source_branch_id_key;
ALTER TABLE transfer_order ADD UNIQUE (identifier, source_branch_id, station_id);

UPDATE till_entry SET station_id = till.station_id FROM till WHERE till.id = till_entry.till_id;
ALTER TABLE till_entry DROP CONSTRAINT till_entry_identifier_branch_id_key;
ALTER TABLE till_entry ADD UNIQUE (identifier, branch_id, station_id);

-- Set not null
ALTER TABLE inventory ALTER station_id SET NOT NULL;
ALTER TABLE loan ALTER station_id SET NOT NULL;
ALTER TABLE payment ALTER station_id SET NOT NULL;
ALTER TABLE payment_renegotiation ALTER station_id SET NOT NULL;
ALTER TABLE production_order ALTER station_id SET NOT NULL;
ALTER TABLE purchase_order ALTER station_id SET NOT NULL;
ALTER TABLE quotation ALTER station_id SET NOT NULL;
ALTER TABLE quote_group ALTER station_id SET NOT NULL;
ALTER TABLE receiving_invoice ALTER station_id SET NOT NULL;
ALTER TABLE receiving_order ALTER station_id SET NOT NULL;
ALTER TABLE returned_sale ALTER station_id SET NOT NULL;
ALTER TABLE sale ALTER station_id SET NOT NULL;
ALTER TABLE stock_decrease ALTER station_id SET NOT NULL;
ALTER TABLE till_entry ALTER station_id SET NOT NULL;
ALTER TABLE transfer_order ALTER station_id SET NOT NULL;
ALTER TABLE work_order ALTER station_id SET NOT NULL;
