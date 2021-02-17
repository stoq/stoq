CREATE TABLE IF NOT EXISTS nfe_supplier (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    cnpj text UNIQUE,
    postal_code text,
    complement text,
    district text,
    street text,
    name text,
    fancy_name text,
    phone_number text,
    municipal_registry text,
    state_registry text,
    city_code INTEGER,
    street_number INTEGER,
    supplier_id uuid REFERENCES supplier(id) ON UPDATE CASCADE
);
CREATE OR REPLACE RULE update_te AS ON UPDATE TO nfe_supplier DO ALSO SELECT update_te(old.te_id);

CREATE TABLE IF NOT EXISTS nfe_purchase (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    invoice_number INTEGER CONSTRAINT valid_invoice_number
        CHECK (invoice_number > 0 AND invoice_number <= 999999999)
        DEFAULT NULL,
    process_date TIMESTAMP,
    cnpj text,
    confirm_purchase BOOLEAN,
    freight_type text,
    freight_cost NUMERIC(20, 2),
    total_cost NUMERIC(20, 2),
    nfe_supplier_id uuid REFERENCES nfe_supplier(id) ON UPDATE CASCADE,
    -- FIXME NOT NULL
    user_id uuid REFERENCES login_user(id) ON UPDATE CASCADE,
    branch_id uuid NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
    purchase_order_id uuid REFERENCES purchase_order(id) ON UPDATE CASCADE,
    invoice_series INTEGER,
    xml xml,
    UNIQUE (invoice_number, invoice_series, nfe_supplier_id)
);
CREATE OR REPLACE RULE update_te AS ON UPDATE TO nfe_purchase DO ALSO SELECT update_te(old.te_id);
DO $$
    BEGIN
        BEGIN
            ALTER TABLE nfe_purchase ADD COLUMN invoice_series INTEGER;
        EXCEPTION
            WHEN duplicate_column THEN RAISE NOTICE 'column invoice_series already exists in nfe_purchase. skipping...';
        END;
    END;
$$;


CREATE TABLE IF NOT EXISTS nfe_item (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    supplier_code text,
    barcode text,
    code text,
    description text,
    quantity NUMERIC(20, 3),
    cost NUMERIC(20, 8) CONSTRAINT positive_cost
        CHECK (cost >= 0),
    discount_value NUMERIC(20, 2) CONSTRAINT positive_discount_value
        CHECK (discount_value >= 0),
    ex_tipi text,
    ncm text,
    genero text,
    nfe_purchase_id uuid NOT NULL REFERENCES nfe_purchase(id) ON UPDATE CASCADE,
    sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE,
    purchase_item_id uuid REFERENCES purchase_item(id) ON UPDATE CASCADE,
    freight_cost NUMERIC(20, 2),
    insurance_cost NUMERIC(20, 2),
    icmsst_cost NUMERIC(20, 2),
    ipi_cost NUMERIC(20, 2)
);


CREATE OR REPLACE RULE update_te AS ON UPDATE TO nfe_item DO ALSO SELECT update_te(old.te_id);


CREATE TABLE IF NOT EXISTS nfe_payment(
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    nfe_purchase_id uuid NOT NULL REFERENCES nfe_purchase(id) ON UPDATE CASCADE,
    method_id uuid REFERENCES payment_method(id) ON UPDATE CASCADE,
    value NUMERIC(20, 2) CONSTRAINT positive_value
        CHECK (VALUE >= 0),
    duplicate_number text,
    due_date TIMESTAMP,
    description text
);
CREATE OR REPLACE RULE update_te AS ON UPDATE TO nfe_payment DO ALSO SELECT update_te(old.te_id);

DO $$
    declare
        p record;
        serie int;
    BEGIN
        FOR p in
            select id, xml, invoice_series from nfe_purchase
        LOOP
            serie := unnest(xpath('//nfe:NFe/nfe:infNFe/nfe:ide/nfe:serie/text()', p.xml ,ARRAY[ARRAY['nfe', 'http://www.portalfiscal.inf.br/nfe']]));
            UPDATE nfe_purchase SET invoice_series=serie where id=p.id;
        END LOOP;
    End;
$$;
