-- Adicionando referencia para branch em payment

ALTER TABLE payment ADD COLUMN branch_id bigint REFERENCES branch(id);
ALTER TABLE quotation ADD COLUMN branch_id bigint REFERENCES branch(id);
ALTER TABLE quote_group ADD COLUMN branch_id bigint REFERENCES branch(id);
ALTER TABLE till_entry ADD COLUMN branch_id bigint REFERENCES branch(id);

-- There may be some quote groups without quotations.
-- Delete them otherwise the update will fail.
DELETE FROM quote_group WHERE id NOT IN (SELECT group_id FROM quotation);

-- Atualizando payments
UPDATE payment SET branch_id = s.branch_id
    FROM sale s WHERE payment.group_id = s.group_id;
UPDATE payment SET branch_id = p.branch_id
    FROM purchase_order p WHERE payment.group_id = p.group_id;
UPDATE payment SET branch_id = r.branch_id
    FROM payment_renegotiation r WHERE payment.group_id = r.group_id;

-- fail safe case: If payment is not in a sale, purchase or renegotiation,
-- use the branch that the object was created. This is the case of lonely
-- payments that dont have a reference to a branch (direct or indirect)
UPDATE payment SET branch_id = s.branch_id
    FROM transaction_entry t, branch_station s
    WHERE payment.branch_id IS NULL
    AND payment.te_created_id = t.id AND t.station_id = s.id;


-- Migrando outras tabelas.
UPDATE quotation SET branch_id = purchase_order.branch_id
    FROM purchase_order WHERE quotation.purchase_id = purchase_order.id;
UPDATE quote_group SET branch_id = quotation.branch_id
    FROM quotation WHERE quote_group.id = quotation.group_id;
UPDATE till_entry SET branch_id = branch_station.branch_id
    FROM till, branch_station
    WHERE till_entry.till_id = till.id AND till.station_id = branch_station.id;


-- Mudando para not null
ALTER TABLE payment ALTER branch_id SET NOT NULL;
ALTER TABLE quotation ALTER branch_id SET NOT NULL;
ALTER TABLE quote_group ALTER branch_id SET NOT NULL;
ALTER TABLE till_entry ALTER branch_id SET NOT NULL;
