-- #3547: Avoid filling in irrelevant data to ProductHistory
UPDATE product_history 
   SET sold_date = NULL, 
       quantity_sold = NULL 
 WHERE quantity_sold = 0;
UPDATE product_history 
   SET received_date = NULL, 
       quantity_received = NULL 
 WHERE quantity_received = 0;
