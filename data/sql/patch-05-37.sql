ALTER TABLE sellable
    ADD COLUMN price_last_updated timestamp DEFAULT NOW(),
    ADD COLUMN cost_last_updated timestamp DEFAULT NOW();
