--
-- Copyright (C) 2006 Async Open Source
--
-- This program is free software; you can redistribute it and/or
-- modify it under the terms of the GNU Lesser General Public License
-- as published by the Free Software Foundation; either version 2
-- of the License, or (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program; if not, write to the Free Software
-- Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
--
--
-- Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
--
--
-- Views and sequences definition for Stoqlib based applications
--


--
-- Functions definitions
--


CREATE OR REPLACE FUNCTION drop_existing_view(text)
--
-- Checks if a certain view exists and drop it. We need this feature
-- since CREATE OR REPLACE statement doesn't apply when changing or
-- adding view attributes.
-- XXX According to developers on postgresql IRC channel there is a bug in
-- the information_schema catalog so we can not fetch a list of user defined
-- views and drop then in one call of this function.
--
RETURNS integer AS '
DECLARE
    view_exists int;
BEGIN

    select into view_exists count(*) from information_schema.views
        where table_name=$1;

    IF view_exists = 1 THEN
        execute ''drop view '' || quote_ident($1) ||'' cascade'';
    END IF;

    RETURN 1;
END;
'  LANGUAGE 'plpgsql';


CREATE OR REPLACE FUNCTION create_stoqlib_sequence(text)
--
-- Checks if a certain sequence exists and create it if it doesn't exists
--
RETURNS integer AS '
DECLARE
    sequence_exists int;
    currschema text;
BEGIN

    select into currschema current_schema();
    select into sequence_exists count(*) from pg_statio_user_sequences
        where schemaname = currschema and relname = $1;

    IF sequence_exists = 0 THEN
        execute ''CREATE SEQUENCE '' || quote_ident($1);
    END IF;

    RETURN 1;
END;
'  LANGUAGE 'plpgsql';


--
-- Sequences
--
-- Note that every sequence name must have a 'stoqlib' prefix to
-- avoid conflicts with SQLObject sequences.
--


select create_stoqlib_sequence('stoqlib_payment_identifier_seq');
select create_stoqlib_sequence('stoqlib_sale_ordernumber_seq');
select create_stoqlib_sequence('stoqlib_purchase_ordernumber_seq');
select create_stoqlib_sequence('stoqlib_sellable_code_seq');
select create_stoqlib_sequence('stoqlib_purchasereceiving_number_seq');
select create_stoqlib_sequence('stoqlib_abstract_bookentry_seq');
select create_stoqlib_sequence('stoqlib_branch_identifier_seq');


--
-- Abstract Views: do not use them on directly on applications
--


select drop_existing_view('abstract_stock_view');
CREATE VIEW abstract_stock_view AS
  --
  -- This is an abstract view which stores stock informations to other views.
  -- Available fields are:
  --     id              - the id of the abstract_sellable table
  --     code            - the product code
  --     barcode         - the product barcode
  --     status          - the product status
  --     stock           - the total amount of stock for a certain product
  --     branch_id       - the id of the person_adapt_to_branch table
  --     stock_cost      - the total cost for the given stock
  --     product_id      - the id of product table
  --
  SELECT DISTINCT
  abstract_sellable.id, abstract_sellable.code, abstract_sellable.barcode,
  abstract_sellable.status,
  abstract_stock_item.quantity + abstract_stock_item.logic_quantity as stock,
  abstract_stock_item.branch_id, abstract_stock_item.stock_cost,
  product.id as product_id
     FROM abstract_stock_item, abstract_sellable, product,
     product_adapt_to_sellable, product_stock_item

        LEFT JOIN product_adapt_to_storable
        ON (product_stock_item.storable_id = product_adapt_to_storable.id)

          WHERE (abstract_stock_item.id = product_stock_item.id
          AND product.id = product_adapt_to_storable.original_id
          AND product.id = product_adapt_to_sellable.original_id
          AND abstract_sellable.id = product_adapt_to_sellable.id);


select drop_existing_view('abstract_product_supplier_view');
CREATE VIEW abstract_product_supplier_view AS
  --
  -- This is an abstract view which stores the main supplier name for all
  -- the products.
  -- Available fields are:
  --     id                 - the id of the product table
  --     supplier_name      - the name of the supplier
  --
  SELECT DISTINCT (product.id), person.name as supplier_name
    FROM product

      LEFT JOIN product_supplier_info
      ON (product_supplier_info.product_id = product.id)

      INNER JOIN person_adapt_to_supplier
      ON (person_adapt_to_supplier.id =
      product_supplier_info.supplier_id)

      INNER JOIN person
      ON (person.id = person_adapt_to_supplier.original_id)

        WHERE product_supplier_info.is_main_supplier = 't';


select drop_existing_view('abstract_sales_client_view');
CREATE VIEW abstract_sales_client_view AS
  --
  -- Stores information about clients tied with sales
  --
  -- Available fields are:
  --     id                 - the id of the sale table
  --     client_id          - the id of the client table
  --     client_name        - the name of the client
  --
  SELECT DISTINCT
  sale.id, sale.client_id, person.name as client_name
    FROM sale

      LEFT JOIN person_adapt_to_client
      ON (sale.client_id = person_adapt_to_client.id)

      LEFT JOIN person
      ON (person_adapt_to_client.original_id = person.id);


select drop_existing_view('abstract_product_item_view');
CREATE VIEW abstract_product_item_view AS
  --
  -- Stores information about abstract_sellable_item objects
  --
  -- Available fields are:
  --     sale_id            - the id of the sale table
  --     quantity           - the quantity sold for a sellable item
  --     subtotal           - the subtotal for a sellable item
  --
  SELECT
  sale_id, quantity, quantity * price as subtotal
    FROM abstract_sellable_item;


select drop_existing_view('abstract_sales_product_view');
CREATE VIEW abstract_sales_product_view AS
  --
  -- Stores information about clients tied with sales
  --
  -- Available fields are:
  --     sale_id            - the id of the sale table
  --     total_quantity     - the total_quantity of sold products
  --     subtotal           - the sale sum of product prices
  --     total              - the sale total value after applying discounts
  --                          and charge
  --
  SELECT
  sum(quantity) as total_quantity,
  sum(subtotal) as subtotal,
  sum(subtotal) - sale.discount_value + sale.surcharge_value as total,
  sale_id
    FROM abstract_product_item_view, sale
      GROUP BY
        sale_id, sale.discount_value, sale.surcharge_value, sale.id
          HAVING
            sale_id = sale.id;


select drop_existing_view('abstract_purchase_product_view');
CREATE VIEW abstract_purchase_product_view AS
  --
  -- Stores information about products tied with purchase orders
  --
  -- Available fields are:
  --     ordered_quantity   - the total ordered products quantity
  --     received_quantity  - the total quantity of received products
  --     subtotal           - the purchase sum of product prices
  --     total              - the purchase total value after applying discounts
  --                          and charge
  --     order_id           - the id of purchase_order table
  --
  SELECT
  sum(quantity) as ordered_quantity,
  sum(quantity_received) as received_quantity,
  sum(cost) as subtotal,
  sum(cost) - purchase_order.discount_value + purchase_order.surcharge_value as total,
  order_id
    FROM purchase_item, purchase_order
      GROUP BY
        order_id, purchase_order.discount_value, purchase_order.surcharge_value,
        purchase_order.id
          HAVING
            order_id = purchase_order.id;


select drop_existing_view('abstract_purchase_transporter_view');
CREATE VIEW abstract_purchase_transporter_view AS
  --
  -- Stores information about transporters tied with purchase orders
  --
  -- Available fields are:
  --     id                 - the id of the purchase_order table
  --     transporter_id     - the id of the person_adapt_to_transporter table
  --     transporter_name   - the name of the transporter
  --
  SELECT DISTINCT
  purchase_order.id, transporter_id, person.name as transporter_name
    FROM purchase_order

      LEFT JOIN person_adapt_to_transporter
      ON (purchase_order.transporter_id = person_adapt_to_transporter.id)

      LEFT JOIN person
      ON (person_adapt_to_transporter.original_id = person.id);


select drop_existing_view('abstract_purchase_branch_view');
CREATE VIEW abstract_purchase_branch_view AS
  --
  -- Stores information about branch companies tied with purchase orders
  --
  -- Available fields are:
  --     id            - the id of the purchase_order table
  --     branch_id     - the id of the person_adapt_to_branch table
  --     branch_name   - the name of the branch
  --
  SELECT DISTINCT
  purchase_order.id, branch_id, person.name as branch_name
    FROM purchase_order

      INNER JOIN person_adapt_to_branch
      ON (purchase_order.branch_id = person_adapt_to_branch.id)

      INNER JOIN person
      ON (person_adapt_to_branch.original_id = person.id);


--
-- Views
--


select drop_existing_view('sellable_view');
CREATE VIEW sellable_view AS
  --
  -- Stores information about sellables. Note: This view must be used
  -- always when searching for stock information on a certain branch
  -- company. For general sellable information in all the branches go to
  -- sellable_full_stock_view.
  --
  -- Usage: select * from sellable_view where branch_id=1;
  --
  -- Available fields are:
  --     id                 - the id of the abstract_sellable table
  --     code               - the sellable code
  --     barcode            - the sellable barcode
  --     status             - the sellable status
  --     stock              - the stock in case the sellable is a product
  --     branch_id          - the if of person_adapt_to_branch table
  --     cost               - the sellable cost
  --     price              - the sellable price
  --     is_valid_model     - the sellable is_valid_model system attribute
  --     description        - the sellable description
  --     unit               - the unit in case the sellable is not a gift
  --                          certificate
  --     supplier_name      - the supplier name in case the sellable is a
  --                          product
  --     product_id         - the id of the product table
  --
  SELECT DISTINCT
  abstract_sellable.id, abstract_sellable.code, abstract_sellable.barcode,
  abstract_sellable.status,
  sum(abstract_stock_view.stock) as stock, abstract_stock_view.branch_id,
  abstract_sellable.cost, base_sellable_info.price,
  base_sellable_info.is_valid_model,
  base_sellable_info.description, sellable_unit.description as unit,
  abstract_product_supplier_view.supplier_name, abstract_stock_view.product_id

    FROM base_sellable_info, abstract_sellable

      LEFT JOIN product_adapt_to_sellable
      ON (abstract_sellable.id = product_adapt_to_sellable.id)

      LEFT JOIN sellable_unit
      ON (abstract_sellable.unit_id = sellable_unit.id)

      LEFT JOIN abstract_stock_view
      ON (abstract_sellable.id = abstract_stock_view.id)

      LEFT JOIN abstract_product_supplier_view
      ON (abstract_stock_view.product_id = abstract_product_supplier_view.id)

        WHERE (abstract_sellable.base_sellable_info_id =
        base_sellable_info.id AND base_sellable_info.is_valid_model = 't')

    group by abstract_sellable.code, abstract_sellable.status,
    abstract_sellable.barcode, abstract_sellable.id,
    abstract_sellable.cost, base_sellable_info.price,
    base_sellable_info.description, sellable_unit.description,
    base_sellable_info.is_valid_model, abstract_stock_view.branch_id,
    abstract_product_supplier_view.supplier_name, abstract_stock_view.product_id;


select drop_existing_view('sellable_full_stock_view');
CREATE VIEW sellable_full_stock_view AS
  --
  -- Stores information about sellables and stock information in all
  -- branch companies.
  --
  -- Available fields are: the same fields of sellable_view table.
  --
  SELECT DISTINCT
  sum(stock) as stock, id, code, barcode, status, 0 as branch_id, cost,
  price, is_valid_model, description, unit, supplier_name, product_id

  FROM sellable_view

    GROUP BY code, barcode, status, id, cost, price, is_valid_model,
    description, unit, supplier_name, product_id;


select drop_existing_view('product_full_stock_view');
CREATE VIEW product_full_stock_view AS
  --
  -- Stores information about products and stock information in all
  -- branch companies.
  --
  -- Available fields are: the same fields of sellable_full_stock_view
  --
  SELECT * FROM sellable_full_stock_view WHERE product_id IS NOT NULL;


select drop_existing_view('service_view');
CREATE VIEW service_view AS
  --
  -- Stores information about services
  --
  -- Available fields are:
  --     id                 - the id of the abstract_sellable table
  --     code               - the sellable code
  --     barcode            - the sellable barcode
  --     status             - the sellable status
  --     cost               - the sellable cost
  --     price              - the sellable price
  --     description        - the sellable description
  --     unit               - the unit in case the sellable is not a gift
  --                          certificate
  --     service_id         - the id of the service table
  --
  SELECT DISTINCT
  abstract_sellable.id, abstract_sellable.code, abstract_sellable.barcode,
  abstract_sellable.status,
  abstract_sellable.cost, base_sellable_info.price,
  base_sellable_info.description, sellable_unit.description as unit,
  service.id as service_id
    FROM abstract_sellable

      INNER JOIN base_sellable_info
      ON (abstract_sellable.base_sellable_info_id = base_sellable_info.id)

      INNER JOIN service_adapt_to_sellable
      ON (abstract_sellable.id = service_adapt_to_sellable.id)

      INNER JOIN service
      ON (service.id = service_adapt_to_sellable.original_id)

      LEFT JOIN sellable_unit
      ON (abstract_sellable.unit_id = sellable_unit.id)

        WHERE service.is_valid_model = 't';


select drop_existing_view('giftcertificate_view');
CREATE VIEW gift_certificate_view AS
  --
  -- Stores information about gift certificates
  --
  -- Available fields are:
  --     id                 - the id of the abstract_sellable table
  --     code               - the sellable code
  --     barcode            - the sellable barcode
  --     status             - the sellable status
  --     cost               - the sellable cost
  --     price              - the sellable price
  --     on_sale_price      - the sellable price when the item is on sale
  --     description        - the sellable description
  --     giftcertificate_id - the id of giftcertificate table
  --
  SELECT DISTINCT
  abstract_sellable.id, abstract_sellable.code, abstract_sellable.barcode,
  abstract_sellable.status,
  abstract_sellable.cost, base_sellable_info.price,
  on_sale_info.on_sale_price,
  base_sellable_info.description, gift_certificate.id as giftcertificate_id
    FROM abstract_sellable

      INNER JOIN base_sellable_info
      ON (abstract_sellable.base_sellable_info_id = base_sellable_info.id)

      INNER JOIN on_sale_info
      ON (abstract_sellable.on_sale_info_id = on_sale_info.id)

      INNER JOIN gift_certificate_adapt_to_sellable
      ON (abstract_sellable.id = gift_certificate_adapt_to_sellable.id)

      INNER JOIN gift_certificate
      ON (gift_certificate_adapt_to_sellable.original_id = gift_certificate.id)

        WHERE gift_certificate.is_valid_model = 't';


select drop_existing_view('sale_view');
CREATE VIEW sale_view AS
  --
  -- Stores information about sales
  --
  -- Available fields are:
  --     id                 - the id of the sale table
  --     coupon_id          - the id generated by the fiscal printer
  --     order_number       - the sale order_number
  --     open_date          - the date when the sale was started
  --     confirm_date       - the date when the sale was confirmed
  --     close_date         - the date when the sale was closed
  --     cancel_date        - the date when the sale was cancelled
  --     notes              - sale order general notes
  --     status             - the sale status
  --     salesperson_name   - the salesperson name
  --     client_name        - the sale client name
  --     client_id          - the if of the client table
  --     subtotal           - the sum of all items in the sale
  --     surcharge_value    - the sale surcharge value
  --     discount_value     - the sale discount value
  --     total              - the subtotal - discount + charge
  --     total_quantity     - the items total quantity for the sale
  --
  SELECT DISTINCT
  sale.id, sale.coupon_id, sale.order_number, sale.open_date,
  sale.close_date, sale.status, person.name as salesperson_name,
  sale.surcharge_value, sale.discount_value, sale.confirm_date,
  sale.cancel_date, sale.notes,
  abstract_sales_client_view.client_name,
  abstract_sales_client_view.client_id,
  abstract_sales_product_view.total,
  abstract_sales_product_view.subtotal,
  abstract_sales_product_view.total_quantity
    FROM sale

      INNER JOIN abstract_sales_client_view
      ON (sale.id = abstract_sales_client_view.id)

      INNER JOIN abstract_sales_product_view
      ON (sale.id = abstract_sales_product_view.sale_id)

      INNER JOIN person_adapt_to_sales_person
      ON (sale.salesperson_id = person_adapt_to_sales_person.id)

      INNER JOIN person
      ON (person_adapt_to_sales_person.original_id = person.id)

        WHERE sale.is_valid_model = 't';


select drop_existing_view('client_view');
CREATE VIEW client_view AS
  --
  -- Stores information about clients.
  -- Available fields are:
  --    id                  - the id of the person table
  --    name                - the client name
  --    status              - the client financial status
  --    cpf                 - the brazil-specific cpf attribute
  --    rg_number           - the brazil-specific rg_number attribute
  --    phone_number        - the client phone_number
  --
  SELECT DISTINCT
  person.id, person.name, person_adapt_to_client.status,
  person_adapt_to_individual.cpf, person_adapt_to_individual.rg_number,
  person.phone_number, person_adapt_to_client.id as client_id
    FROM person

      LEFT JOIN person_adapt_to_individual
      ON (person.id = person_adapt_to_individual.original_id)

      INNER JOIN person_adapt_to_client
      ON (person.id = person_adapt_to_client.original_id)

        WHERE person_adapt_to_client.is_valid_model = 't';


select drop_existing_view('purchase_order_view');
CREATE VIEW purchase_order_view AS
  --
  -- Stores information about purchase orders.
  -- Available fields are:
  --    id                      - the if of purchase_order table
  --    status                  - the purchase order status
  --    order_number            - the purchase order_number
  --    open_date               - the date when the order was started
  --    quote_deadline          - the date when the quotation expires
  --    expected_receival_date  - expected date to receive products
  --    expected_pay_date       - expected date to pay the products
  --    receival_date           - the date when the products were received
  --    confirm_date            - the date when the order was confirmed
  --    salesperson_name        - the name of supplier's salesperson
  --    freight                 - the freight value
  --    surcharge_value         - the surcharge value for the order total
  --    discount_value          - the discount_value for the order total
  --    supplier_name           - the supplier name
  --    transporter_name        - the transporter name
  --    branch_name             - the branch company name
  --    ordered_quantity        - the total quantity ordered
  --    received_quantity       - the total quantity received
  --    subtotal                - the order subtotal (sum of product values)
  --    total                   - subtotal - discount_value + surcharge_value
  --
  SELECT DISTINCT
  purchase_order.id, purchase_order.status, purchase_order.order_number,
  purchase_order.open_date, purchase_order.quote_deadline,
  purchase_order.expected_receival_date,
  purchase_order.expected_pay_date, purchase_order.receival_date,
  purchase_order.confirm_date, purchase_order.salesperson_name,
  purchase_order.freight, purchase_order.surcharge_value,
  purchase_order.discount_value, person.name as supplier_name,
  abstract_purchase_transporter_view.transporter_name,
  abstract_purchase_branch_view.branch_name,
  abstract_purchase_product_view.ordered_quantity,
  abstract_purchase_product_view.received_quantity,
  abstract_purchase_product_view.subtotal,
  abstract_purchase_product_view.total
    FROM purchase_order

      INNER JOIN person_adapt_to_supplier
      ON (purchase_order.supplier_id = person_adapt_to_supplier.id)

      INNER JOIN person
      ON (person_adapt_to_supplier.original_id = person.id)

      INNER JOIN abstract_purchase_transporter_view
      ON (purchase_order.id = abstract_purchase_transporter_view.id)

      INNER JOIN abstract_purchase_branch_view
      ON (purchase_order.id = abstract_purchase_branch_view.id)

      INNER JOIN abstract_purchase_product_view
      ON (purchase_order.id = abstract_purchase_product_view.order_id)

        WHERE purchase_order.is_valid_model = 't';


select drop_existing_view('icms_ipi_view');
CREATE VIEW icms_ipi_view AS
  --
  -- Stores information about clients.
  -- Available fields are:
  --    id                  - the id of the icms_ipi_book_entry table
  --    identifier          - the identifier of icms_ipi_book_entry table
  --    icms_value          - the total value of icms
  --    ipi_value           - the total value of ipi
  --    date                - the date when the entry was created
  --    invoice_number      - the invoice number
  --    cfop_data_id        - the if of the cfop_data table
  --    cfop_code           - the code of the cfop
  --    drawee_name         - the drawee name
  --    drawee_id           - the if of Person table
  --    branch_id           - the id of the person_adapt_to_branch table
  --    payment_group_id    - the id of the abstract_payment_group table
  --
  SELECT DISTINCT
  icms_ipi_book_entry.id,
  icms_ipi_book_entry.icms_value,
  icms_ipi_book_entry.ipi_value,

  abstract_fiscal_book_entry.identifier,
  abstract_fiscal_book_entry.date,
  abstract_fiscal_book_entry.invoice_number,
  abstract_fiscal_book_entry.cfop_id as cfop_data_id,
  abstract_fiscal_book_entry.branch_id,
  abstract_fiscal_book_entry.drawee_id,
  abstract_fiscal_book_entry.payment_group_id,

  cfop_data.code as cfop_code,
  person.name as drawee_name

    FROM icms_ipi_book_entry

      INNER JOIN abstract_fiscal_book_entry
      ON (icms_ipi_book_entry.id = abstract_fiscal_book_entry.id)

      INNER JOIN cfop_data
      ON (cfop_data.id = abstract_fiscal_book_entry.cfop_id)

      LEFT JOIN person
      ON (abstract_fiscal_book_entry.drawee_id = person.id);


select drop_existing_view('iss_view');
CREATE VIEW iss_view AS
  --
  -- Stores information about clients.
  -- Available fields are:
  --    id                  - the id of the iss_book_entry table
  --    identifier          - the identifier of iss_book_entry table
  --    iss_value           - the total value of iss
  --    date                - the date when the entry was created
  --    invoice_number      - the invoice number
  --    cfop_data_id        - the if of the cfop_data table
  --    cfop_code           - the code of the cfop
  --    drawee_name         - the drawee name
  --    branch_id           - the id of the person_adapt_to_branch table
  --    payment_group_id    - the if of the abstract_payment_group table
  --
  SELECT DISTINCT
  iss_book_entry.id,
  iss_book_entry.iss_value,

  abstract_fiscal_book_entry.identifier,
  abstract_fiscal_book_entry.date,
  abstract_fiscal_book_entry.invoice_number,
  abstract_fiscal_book_entry.cfop_id as cfop_data_id,
  abstract_fiscal_book_entry.branch_id,
  abstract_fiscal_book_entry.drawee_id,
  abstract_fiscal_book_entry.payment_group_id,

  cfop_data.code as cfop_code,
  person.name as drawee_name

    FROM iss_book_entry

      INNER JOIN abstract_fiscal_book_entry
      ON (iss_book_entry.id = abstract_fiscal_book_entry.id)

      INNER JOIN cfop_data
      ON (cfop_data.id = abstract_fiscal_book_entry.cfop_id)

      LEFT JOIN person
      ON (abstract_fiscal_book_entry.drawee_id = person.id);
