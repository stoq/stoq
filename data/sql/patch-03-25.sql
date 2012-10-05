-- #5106: Criar novo campo sigla, para Branches

ALTER TABLE branch ADD COLUMN acronym text UNIQUE
    CONSTRAINT acronym_not_empty CHECK (acronym != '');
