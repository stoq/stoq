--
-- Creation of magento_config, magento_client, magento_address,
-- magento_product, magento_stock, magento_sale, magento_invoice.
--

CREATE TABLE magento_config (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    url text UNIQUE NOT NULL,
    api_user text NOT NULL,
    api_key text NOT NULL,
    qty_days_as_new integer,
    tz_hours numeric(10, 2),
    branch_id bigint UNIQUE REFERENCES person_adapt_to_branch(id),
    salesperson_id bigint UNIQUE REFERENCES person_adapt_to_sales_person(id)
);

CREATE TABLE magento_table_dict (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    magento_table text NOT NULL,
    config_id bigint REFERENCES magento_config(id)
);

CREATE TABLE magento_table_dict_item (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    item_key text,
    item_value text,
    item_type text,
    mapper_id bigint REFERENCES magento_table_dict(id)
);

CREATE TABLE magento_product (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    magento_id bigint,
    need_sync boolean,
    sku text,
    visibility integer,
    product_type text,
    product_set integer,
    url_key text,
    news_from_date timestamp,
    news_to_date timestamp,
    config_id bigint REFERENCES magento_config(id),
    product_id bigint UNIQUE REFERENCES product(id)
);

CREATE TABLE magento_stock (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    magento_id bigint,
    need_sync boolean,
    config_id bigint REFERENCES magento_config(id),
    magento_product_id bigint UNIQUE REFERENCES magento_product(id)
);

CREATE TABLE magento_image (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    magento_id bigint,
    need_sync boolean,
    is_main boolean,
    visible boolean,
    image bytea,
    filename text,
    label text,
    config_id bigint REFERENCES magento_config(id),
    magento_product_id bigint REFERENCES magento_product(id)
);

CREATE TABLE magento_client (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    magento_id bigint,
    need_sync boolean,
    config_id bigint REFERENCES magento_config(id),
    client_id bigint UNIQUE REFERENCES person_adapt_to_client(id)
);

CREATE TABLE magento_address (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    magento_id bigint,
    need_sync boolean,
    config_id bigint REFERENCES magento_config(id),
    magento_client_id bigint REFERENCES magento_client(id),
    address_id bigint UNIQUE REFERENCES address(id)
);

CREATE TABLE magento_sale (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    magento_id bigint,
    need_sync boolean,
    status text,
    config_id bigint REFERENCES magento_config(id),
    magento_client_id bigint REFERENCES magento_client(id),
    sale_id bigint UNIQUE REFERENCES sale(id)
);

CREATE TABLE magento_invoice (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    magento_id bigint,
    need_sync boolean,
    status integer,
    can_void boolean,
    config_id bigint REFERENCES magento_config(id),
    magento_sale_id bigint REFERENCES magento_sale(id)
);

CREATE TABLE magento_shipment (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    magento_id bigint,
    need_sync boolean,
    was_track_added boolean,
    config_id bigint REFERENCES magento_config(id),
    magento_sale_id bigint REFERENCES magento_sale(id)
);


