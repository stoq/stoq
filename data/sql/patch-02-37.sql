-- Add 'description' column in 'calls' table to a short comment of call.

ALTER TABLE calls ADD COLUMN description text;
