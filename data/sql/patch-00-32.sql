-- #3610: Inserir CPF e CNPJ ao finalizar venda para atender as
-- exigências da N.F. Paulista.

-- Create paulista_invoice table
CREATE TABLE paulista_invoice (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    sale_id bigint REFERENCES sale(id),
    document_type integer CONSTRAINT valid_type CHECK (document_type = 0 OR document_type = 1),
    document text
);
