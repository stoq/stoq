ALTER TABLE person_adapt_to_publisher RENAME TO book_publisher;
ALTER SEQUENCE person_adapt_to_publisher_id_seq RENAME TO book_publisher_id_seq;

ALTER TABLE book_publisher RENAME COLUMN original_id TO person_id;

ALTER TABLE product_adapt_to_book RENAME TO book;
ALTER SEQUENCE product_adapt_to_book_id_seq RENAME TO book_id_seq;

ALTER TABLE book RENAME COLUMN original_id TO product_id;
