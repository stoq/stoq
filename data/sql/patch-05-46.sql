-- We need to disable the update_te or else we will not be able to get
-- the original transaction_entry.te_time from it
ALTER TABLE image DISABLE RULE update_te;

ALTER TABLE image ADD sellable_id uuid REFERENCES sellable(id) ON UPDATE CASCADE;
ALTER TABLE image ADD is_main boolean DEFAULT false;
ALTER TABLE image ADD internal_use boolean DEFAULT false;
ALTER TABLE image ADD notes text;
ALTER TABLE image ADD create_date timestamp NOT NULL DEFAULT statement_timestamp();
ALTER TABLE image ADD filename text;

-- TODO: make is_main unique
UPDATE image SET sellable_id = sellable.id, is_main = true, create_date = transaction_entry.te_time
  FROM sellable, transaction_entry
  WHERE sellable.image_id = image.id AND transaction_entry.id = image.te_id;
-- The thumbnail size changed, make sure we will regenarete them
-- Also set a default filename to the main images
UPDATE image SET thumbnail = NULL, filename = 'main_image.png';

-- Reenable the rule and run it on all images. All of them should have been
-- affected because of the migration above
ALTER TABLE image ENABLE RULE update_te;
SELECT update_te(te_id) FROM image;

ALTER TABLE sellable DROP COLUMN image_id;
