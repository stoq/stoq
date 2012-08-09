-- Adicionando referencia para branch em payment

ALTER TABLE payment ADD COLUMN branch_id bigint REFERENCES branch(id);

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

ALTER TABLE payment ALTER branch_id SET NOT NULL;
