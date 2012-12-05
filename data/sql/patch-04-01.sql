-- Patch for bug 5295
-- This bug reverses naming of interest and penalty to set it straight.
-- Hence the renaming of columns.

ALTER TABLE payment_method
    ADD daily_interest numeric(10, 2) CONSTRAINT valid_daily_interest
	CHECK (daily_interest >= 0 AND daily_interest <= 100),
    ADD penalty numeric(10, 2) CONSTRAINT penalty_percent
	CHECK (penalty >= 0 AND penalty <= 100);

UPDATE payment_method SET daily_interest = daily_penalty, penalty = interest;

ALTER TABLE payment_method
    DROP daily_penalty,
    DROP interest;
