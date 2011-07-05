-- #4444: Multa como porcentagem
ALTER TABLE payment DROP CONSTRAINT interest_percent;
ALTER TABLE payment ADD CONSTRAINT interest_percent
        CHECK (interest >= 0);
