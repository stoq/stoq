-- Bug 3893 - Adicionar data de validade para orçamentos

ALTER TABLE sale ADD COLUMN expire_date timestamp;
