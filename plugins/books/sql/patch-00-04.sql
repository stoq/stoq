CREATE TYPE book_publisher_status AS ENUM ('active', 'inactive');

ALTER TABLE book_publisher ADD COLUMN temp_status integer;
UPDATE book_publisher SET temp_status = status;
ALTER TABLE book_publisher DROP CONSTRAINT valid_status;
ALTER TABLE book_publisher ALTER COLUMN status DROP NOT NULL;
ALTER TABLE book_publisher
    ALTER COLUMN status TYPE book_publisher_status USING 'active';
UPDATE book_publisher SET status = 'active' WHERE temp_status = 0;
UPDATE book_publisher SET status = 'inactive' WHERE temp_status = 1;
ALTER TABLE book_publisher DROP COLUMN temp_status;
ALTER TABLE book_publisher ALTER COLUMN status SET NOT NULL;
