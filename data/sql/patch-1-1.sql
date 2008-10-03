-- #3821: Sale's client and Purchase's Supplier should be saved in Payment Group
UPDATE payment_group
   SET payer_id = person.id
  FROM sale, person_adapt_to_client, person
 WHERE payment_group.payer_id is NULL AND
       sale.group_id = payment_group.id AND
       person_adapt_to_client.id = sale.client_id AND
       person.id = person_adapt_to_client.original_id;

UPDATE payment_group
   SET recipient_id = person.id
  FROM purchase_order, person_adapt_to_supplier, person
 WHERE payment_group.recipient_id is NULL AND
       purchase_order.group_id = payment_group.id AND
       person_adapt_to_supplier.id = purchase_order.supplier_id AND
       person.id = person_adapt_to_supplier.original_id;
