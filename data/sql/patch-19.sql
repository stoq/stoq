CREATE TABLE commission_source (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint REFERENCES transaction_entry(id),
    te_modified_id bigint REFERENCES transaction_entry(id),

    direct_value numeric(10, 2) NOT NULL CONSTRAINT positive_value
        CHECK (direct_value >= 0),
    installments_value numeric(10, 2) NOT NULL CONSTRAINT positive_installments_value
        CHECK (installments_value >= 0),
    category_id bigint REFERENCES sellable_category(id),
    asellable_id bigint REFERENCES asellable(id),
    -- only one reference will exist at a time: category_id or asellable_id
    -- never both or none of them
    CONSTRAINT check_exist_one_fkey
        CHECK (category_id IS NOT NULL AND asellable_id IS NULL OR
               category_id IS NULL and asellable_id IS NOT NULL)
    );

CREATE TABLE commission (
    id serial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint REFERENCES transaction_entry(id),
    te_modified_id bigint REFERENCES transaction_entry(id),

    value numeric(10, 2) NOT NULL CONSTRAINT positive_value CHECK (value >= 0),
    commission_type integer NOT NULL,
    salesperson_id bigint NOT NULL REFERENCES person_adapt_to_sales_person(id),
    sale_id bigint NOT NULL REFERENCES sale(id),
    payment_id bigint NOT NULL UNIQUE REFERENCES payment(id)
   );
