ALTER TABLE person_adapt_to_publisher RENAME TO book_publisher;

ALTER TABLE book_publisher RENAME COLUMN original_id TO person_id;

ALTER TABLE product_adapt_to_book RENAME TO book;

ALTER TABLE book RENAME COLUMN original_id TO product_id;
