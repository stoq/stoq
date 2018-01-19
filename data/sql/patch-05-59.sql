CREATE TABLE receiving_invoice (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    identifier SERIAL NOT NULL,
    invoice_number INTEGER CONSTRAINT valid_invoice_number CHECK (invoice_number > 0 AND invoice_number <= 999999999),
    invoice_series INTEGER,
    invoice_key TEXT,
    freight_total NUMERIC(20, 2) CONSTRAINT freight_total CHECK (freight_total >= 0),
    surcharge_value NUMERIC(20, 2) CONSTRAINT positive_surcharge CHECK (surcharge_value >= 0),
    discount_value NUMERIC(20, 2) CONSTRAINT positive_discount CHECK (discount_value >= 0),
    icms_total NUMERIC(20, 2),
    icms_st_total NUMERIC(20, 2),
    ipi_total NUMERIC(20, 2),
    expense_value NUMERIC(20, 2) CONSTRAINT positive_expense CHECK (expense_value >= 0),
    secure_value NUMERIC(20, 2) CONSTRAINT positive_secure CHECK (secure_value >= 0),
    invoice_total NUMERIC(20, 2),
    freight_type receiving_order_freight_type DEFAULT 'fob-payment' NOT NULL,
    notes TEXT,
    branch_id UUID REFERENCES branch(id) ON UPDATE CASCADE,
    group_id UUID REFERENCES payment_group(id) ON UPDATE CASCADE,
    supplier_id UUID REFERENCES supplier(id) ON UPDATE CASCADE,
    transporter_id UUID REFERENCES transporter(id) ON UPDATE CASCADE,
    responsible_id UUID REFERENCES login_user(id) ON UPDATE CASCADE,
    UNIQUE (invoice_number, invoice_series, supplier_id)
);

ALTER TABLE receiving_order
    ADD packing_number TEXT,
    ADD receiving_invoice_id UUID REFERENCES receiving_invoice(id) ON UPDATE CASCADE;

INSERT INTO receiving_invoice (identifier, invoice_number, invoice_key, freight_total, surcharge_value, discount_value, icms_total, ipi_total,
                               expense_value, secure_value, invoice_total, freight_type, branch_id, transporter_id, supplier_id, responsible_id)
            SELECT identifier, invoice_number, invoice_key, freight_total, surcharge_value, discount_value, icms_total, ipi_total,
                   expense_value, secure_value, invoice_total, freight_type, branch_id, transporter_id, supplier_id, responsible_id
                   FROM receiving_order;

UPDATE receiving_order SET receiving_invoice_id = receiving_invoice.id
    FROM receiving_invoice
    WHERE receiving_order.identifier = receiving_invoice.identifier AND
          receiving_order.branch_id = receiving_invoice.branch_id;

SELECT setval('receiving_invoice_identifier_seq', (SELECT MAX(identifier) FROM receiving_invoice));

ALTER TABLE receiving_order
    DROP COLUMN invoice_key,
    DROP COLUMN freight_total,
    DROP COLUMN surcharge_value,
    DROP COLUMN discount_value,
    DROP COLUMN icms_total,
    DROP COLUMN ipi_total,
    DROP COLUMN expense_value,
    DROP COLUMN secure_value,
    DROP COLUMN invoice_total,
    DROP COLUMN freight_type,
    DROP COLUMN supplier_id,
    DROP COLUMN transporter_id;
