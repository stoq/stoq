-- Those indexes are created to accelerate queries with lots of sellables
-- using like/ilike comparisons
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE INDEX sellable_description_idx ON sellable
    USING gist (description gist_trgm_ops);
CREATE INDEX sellable_description_normalized_idx ON sellable
    USING gist (stoq_normalize_string(description) gist_trgm_ops);
