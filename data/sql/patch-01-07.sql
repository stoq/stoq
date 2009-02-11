-- Bug 3702 - Adiconar método 'Fiado'

ALTER TABLE person_adapt_to_client
    ADD COLUMN credit_limit numeric(10,2) DEFAULT 0
    CONSTRAINT positive_credit_limit CHECK (credit_limit >= 0);
