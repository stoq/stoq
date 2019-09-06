ALTER TABLE sellable ADD COLUMN requires_kitchen_production BOOLEAN;
ALTER TABLE sellable_branch_override ADD COLUMN requires_kitchen_production BOOLEAN;
ALTER TABLE branch_station ADD COLUMN has_kps_enabled BOOLEAN;
