-- Add Mercosul details

ALTER TABLE product
    ADD COLUMN ncm text,
    ADD COLUMN ex_tipi text,
    ADD COLUMN genero text;
