-- Bug 3709 - Store ecf documents information

CREATE TABLE ecf_document_history (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id),
    printer_id uuid NOT NULL REFERENCES ecf_printer(id),
    type integer CONSTRAINT valid_type CHECK (type >= 0 AND type < 3),
    coo integer NOT NULL CONSTRAINT coo_positive CHECK (coo >= 0),
    gnf integer NOT NULL CONSTRAINT gnf_positive CHECK (gnf >= 0),
    crz integer,
    emission_date timestamp NOT NULL CONSTRAINT past_emission_date CHECK (emission_date <= NOW())
);

