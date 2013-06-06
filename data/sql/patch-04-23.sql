-- User profiles now have roles associated with them. These allows managers to
-- apply discounts bigger than the normally allowed for sellables.

ALTER TABLE user_profile ADD COLUMN max_discount numeric(10, 2) DEFAULT 0;
