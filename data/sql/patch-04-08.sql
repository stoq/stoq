-- 5375: Anexar comprovante de pagamento a contas a pagar

CREATE TABLE attachment (
    id serial NOT NULL PRIMARY KEY,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),
    name text NOT NULL,
    mimetype text,
    blob bytea
);

ALTER TABLE payment
    ADD COLUMN attachment_id bigint UNIQUE REFERENCES attachment(id)
        ON UPDATE CASCADE;
