-- #2507: Incluir suporte à impressão de nota fiscal

CREATE TABLE invoice_layout (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint REFERENCES transaction_entry(id),
    te_modified_id bigint REFERENCES transaction_entry(id),

    description varchar NOT NULL,
    width bigint NOT NULL CONSTRAINT positive_width CHECK (width > 0),
    height bigint NOT NULL CONSTRAINT positive_height CHECK (height > 0)
    );

CREATE TABLE invoice_field (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint REFERENCES transaction_entry(id),
    te_modified_id bigint REFERENCES transaction_entry(id),

    field_name varchar NOT NULL,
    layout_id bigint REFERENCES invoice_layout(id),
    x bigint NOT NULL CONSTRAINT positive_x CHECK (x >= 0),
    y bigint NOT NULL CONSTRAINT positive_y CHECK (y >= 0),
    width bigint NOT NULL CONSTRAINT positive_width CHECK (width > 0),
    height bigint NOT NULL CONSTRAINT positive_height CHECK (height > 0)
   );

CREATE TABLE invoice_printer (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint REFERENCES transaction_entry(id),
    te_modified_id bigint REFERENCES transaction_entry(id),

    device_name varchar NOT NULL,
    description varchar NOT NULL,
    station_id bigint REFERENCES branch_station(id),
    layout_id bigint REFERENCES invoice_layout(id)
    );
