-- #3913: Na forma de pagamento cartao, nao e possível definir percentuais das
-- administradoras.

ALTER TABLE person_adapt_to_credit_provider
    ADD COLUMN provider_fee numeric(10, 4) NOT NULL DEFAULT 0
        CONSTRAINT positive_provider_fee CHECK (provider_fee >= 0);
