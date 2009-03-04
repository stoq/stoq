-- #3882 Adiconar orcamento de vendas

ALTER TABLE sale DROP CONSTRAINT valid_status;

ALTER TABLE sale ADD CONSTRAINT valid_status
    CHECK (status >= 0 AND status < 7);
