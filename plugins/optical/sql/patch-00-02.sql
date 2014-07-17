-- Add partner field to medic

ALTER TABLE optical_medic ADD COLUMN partner boolean DEFAULT FALSE NOT NULL;
