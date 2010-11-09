-- Creation of taxes tables


CREATE TABLE product_tax_template (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    name text,
    tax_type integer
);


--
--  Product Template Classes
--

CREATE TABLE product_icms_template (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    product_tax_template_id bigint UNIQUE REFERENCES product_tax_template(id),

    orig integer,
    cst integer,
    mod_bc integer,
    p_icms numeric(10,2),

    mod_bc_st integer,
    p_mva_st numeric(10,2),
    p_red_bc_st numeric(10,2),
    p_icms_st numeric(10,2),
    p_red_bc numeric(10,2)
);


CREATE TABLE product_ipi_template (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    product_tax_template_id bigint UNIQUE REFERENCES product_tax_template(id),

    cl_enq text,
    cnpj_prod text,
    c_selo text,
    q_selo integer,
    c_enq text,

    cst integer,
    p_ipi numeric(10, 2),
    q_unid numeric(10, 4)
);


--
--  Sale Item Classes
--

CREATE TABLE sale_item_icms (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    orig integer,
    cst integer,
    mod_bc integer,
    p_icms numeric(10,2),

    mod_bc_st integer,
    p_mva_st numeric(10,2),
    p_red_bc_st numeric(10,2),
    p_icms_st numeric(10,2),
    p_red_bc numeric(10,2),

    v_bc numeric(10,2),
    v_icms numeric(10,2),
    v_bc_st numeric(10,2),
    v_icms_st numeric(10,2)

);


CREATE TABLE sale_item_ipi (
    id bigserial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

    cl_enq text,
    cnpj_prod text,
    c_selo text,
    q_selo integer,
    c_enq text,

    cst integer,
    p_ipi numeric(10, 2),
    q_unid numeric(10, 4),

    v_ipi numeric(10, 2),
    v_bc numeric(10, 2),
    v_unid numeric(10, 4)
);



ALTER TABLE sale_item ADD COLUMN icms_info_id bigint REFERENCES
    sale_item_icms(id);

ALTER TABLE product
    ADD COLUMN icms_template_id bigint REFERENCES product_icms_template(id),
    ADD COLUMN ipi_template_id bigint REFERENCES product_ipi_template(id);
