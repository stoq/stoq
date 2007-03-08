--
-- Copyright (C) 2006,2007 Async Open Source
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
--                  Johan Dahlin                <jdahlin@async.com.br>
--

--
-- Views
--


--
-- Stores information about sellables. Note: This view must be used
-- always when searching for stock information on a certain branch
-- company. For general sellable information in all the branches go to
-- sellable_full_stock_view.
--
-- Usage: select * from sellable_view where branch_id=1;
--
-- Available fields are:
--     id                 - the id of the asellable table
--     code               - the sellable code
--     barcode            - the sellable barcode
--     status             - the sellable status
--     cost               - the sellable cost
--     price              - the sellable price
--     is_valid_model     - the sellable is_valid_model system attribute
--     description        - the sellable description
--     unit               - the unit in case the sellable is not a gift
--                          certificate
--     product_id         - the id of the product table
--     supplier_name      - the supplier name in case the sellable is a
--                          product
--     branch_id          - the id of person_adapt_to_branch table
--     stock              - the stock in case the sellable is a product
--
--
--
-- Callsites:
--
--   stoqlib/gui/search/sellablesearch.py
--   stoqlib/reporting/product.py
--
CREATE VIEW sellable_view AS

   SELECT DISTINCT
      asellable.id AS id,
      asellable.code AS code,
      asellable.barcode AS barcode,
      asellable.status AS status,
      asellable.cost AS cost,
      base_sellable_info.price AS price,
      base_sellable_info.is_valid_model AS is_valid_model,
      base_sellable_info.description AS description,
      sellable_unit.description AS unit,
      product.id as product_id,
      supplier_person.name AS supplier_name,
      abstract_stock_item.branch_id AS branch_id,
      sum(abstract_stock_item.quantity+abstract_stock_item.logic_quantity) AS stock

   FROM base_sellable_info, asellable

      -- Sellable unit

      LEFT JOIN sellable_unit
      ON (sellable_unit.id = asellable.unit_id)

      -- Product

      LEFT JOIN product_adapt_to_sellable
      ON (product_adapt_to_sellable.id = asellable.id)

      LEFT JOIN product
      ON (product.id = product_adapt_to_sellable.original_id)

      -- Product Stock Item

      LEFT JOIN product_adapt_to_storable
      ON (product_adapt_to_storable.original_id = product.id)
      
      LEFT JOIN product_stock_item
      ON (product_stock_item.storable_id = product_adapt_to_storable.id)

      LEFT JOIN abstract_stock_item
      ON (abstract_stock_item.id = product_stock_item.id)

      -- Product Supplier

      LEFT JOIN product_supplier_info
      ON (product_supplier_info.product_id = product.id AND
          product_supplier_info.is_main_supplier = 't')

      LEFT JOIN person_adapt_to_supplier
      ON (person_adapt_to_supplier.id = product_supplier_info.supplier_id)

      LEFT JOIN person AS supplier_person
      ON (supplier_person.id = person_adapt_to_supplier.original_id)

   WHERE
        asellable.base_sellable_info_id = base_sellable_info.id AND
        base_sellable_info.is_valid_model = 't'

   GROUP BY
        asellable.code, asellable.status,  asellable.barcode, asellable.id, 
        asellable.cost, base_sellable_info.price, base_sellable_info.description, 
        base_sellable_info.is_valid_model, sellable_unit.description, 
        product.id,  supplier_person.name, abstract_stock_item.branch_id;



--
-- Stores information about sellables and stock information in all
-- branch companies.
--
-- Available fields are: the same fields of sellable_view table.
--
-- Callsites:
--
--   stoqlib/gui/search/sellablesearch.py
--
CREATE VIEW sellable_full_stock_view AS

  SELECT DISTINCT
    sum(stock) AS stock,
    id,
    code,
    barcode,
    status,
    0 AS branch_id, cost,
    price,
    is_valid_model,
    description,
    unit,
    supplier_name,
    product_id

  FROM sellable_view

  GROUP BY code, barcode, status, id, cost, price, is_valid_model,
           description, unit, supplier_name, product_id;


--
-- Stores information about services
--
-- Available fields are:
--     id                 - the id of the asellable table
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
-- Callsites:
--
--   stoqlib/gui/search/servicesearch.py
--
CREATE VIEW service_view AS

  SELECT DISTINCT
    asellable.id AS id,
    asellable.code AS code,
    asellable.barcode AS barcode,
    asellable.status AS status,
    asellable.cost AS cost,
    base_sellable_info.price AS price,
    base_sellable_info.description AS description,
    sellable_unit.description AS unit,
    service.id AS service_id

  FROM base_sellable_info, service_adapt_to_sellable, service, asellable

    LEFT JOIN sellable_unit
    ON (asellable.unit_id = sellable_unit.id)

  WHERE service.is_valid_model = 't' AND
        asellable.base_sellable_info_id = base_sellable_info.id AND
        asellable.id = service_adapt_to_sellable.id AND
        service.id = service_adapt_to_sellable.original_id;


--
-- Stores information about gift certificates
--
-- Available fields are:
--     id                 - the id of the asellable table
--     code               - the sellable code
--     barcode            - the sellable barcode
--     status             - the sellable status
--     cost               - the sellable cost
--     price              - the sellable price
--     on_sale_price      - the sellable price when the item is on sale
--     description        - the sellable description
--     giftcertificate_id - the id of giftcertificate table
--
-- Callsites:
--
--   stoqlib/gui/search/giftcertificatesearch.py
--
CREATE VIEW gift_certificate_view AS

  SELECT DISTINCT
    asellable.id AS id,
    asellable.code AS code,
    asellable.barcode AS barcode,
    asellable.status AS status,
    asellable.cost AS cost,
    base_sellable_info.price AS price,
    on_sale_info.on_sale_price AS on_sale_price,
    base_sellable_info.description AS description,
    gift_certificate.id AS giftcertificate_id

  FROM asellable, base_sellable_info, on_sale_info, 
       gift_certificate_adapt_to_sellable, gift_certificate

  WHERE gift_certificate.is_valid_model = 't' AND
        asellable.base_sellable_info_id = base_sellable_info.id AND
        asellable.on_sale_info_id = on_sale_info.id AND
        asellable.id = gift_certificate_adapt_to_sellable.id AND
        gift_certificate_adapt_to_sellable.original_id = gift_certificate.id;

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
--  Callsites:
--   
--   stoqlib/domain/person.py
--   stoqlib/gui/search/salesearch.py
--   stoqlib/gui/slaves/saleslave.py
--   stoqlib/gui/dialogs/saledetails.p
--   stoqlib/gui/wizards/salereturnwizard.py
--   stoqlib/reporting/sale.py
--   stoq/gui/receivable/receivable.py
--   stoq/gui/sales/sales.py
--   stoq/gui/till/till.py
--
CREATE VIEW sale_view AS

  SELECT DISTINCT
    sale_id AS id,
    sale.coupon_id AS coupon_id,
    sale.order_number AS order_number,
    sale.open_date AS open_date,
    sale.close_date AS close_date,
    sale.status AS status,
    sale.surcharge_value AS surcharge_value,
    sale.discount_value AS discount_value,
    sale.confirm_date AS confirm_date,
    sale.cancel_date AS cancel_date,
    sale.notes AS notes,
    sale.client_id AS client_id,
    client_person.name AS client_name,
    person.name AS salesperson_name,
    sum(quantity * price) - sale.discount_value + sale.surcharge_value AS total,
    sum(quantity * price) AS subtotal,
    sum(quantity) AS total_quantity

  FROM asellable_item, person_adapt_to_sales_person, person, sale
    
    LEFT JOIN person_adapt_to_client
    ON (sale.client_id = person_adapt_to_client.id)

    LEFT JOIN person AS client_person
    ON (person_adapt_to_client.original_id = client_person.id)

  WHERE sale.is_valid_model = 't' AND
        asellable_item.sale_id = sale_id AND
        sale.salesperson_id = person_adapt_to_sales_person.id AND
        person_adapt_to_sales_person.original_id = person.id
 
  GROUP BY asellable_item.sale_id, sale.id,
           sale.surcharge_value, sale.discount_value, 
           sale.coupon_id, sale.order_number,
           sale.open_date, sale.close_date,
           sale.status, sale.confirm_date,
           sale.cancel_date, sale.notes,
           sale.client_id,
           client_person.name,
           person.name

  HAVING sale_id = sale.id;

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
-- Callsites:
--
--   stoqlib/gui/search/personsearch.py
--
CREATE VIEW client_view AS

  SELECT DISTINCT
    person.id AS id,
    person.name AS name,
    person_adapt_to_client.status AS status,
    person_adapt_to_individual.cpf AS cpf,
    person_adapt_to_individual.rg_number As rg_number,
    person.phone_number AS phone_number,
    person_adapt_to_client.id AS client_id

  FROM person_adapt_to_client, person

    LEFT JOIN person_adapt_to_individual
    ON (person.id = person_adapt_to_individual.original_id)

  WHERE person_adapt_to_client.is_valid_model = 't' AND
        person.id = person_adapt_to_client.original_id;


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
-- Callsites:
--
--   stoqlib/gui/wizards/receivingwizard.py
--   stoqlib/reporting/purchase.py
--   stoq/gui/purchase/purchase.py
--
CREATE VIEW purchase_order_view AS

  SELECT DISTINCT
    purchase_order.id AS id,
    purchase_order.status AS status,
    purchase_order.order_number AS order_number,
    purchase_order.open_date AS open_date,
    purchase_order.quote_deadline AS quote_deadline,
    purchase_order.expected_receival_date AS expected_receival_date,
    purchase_order.expected_pay_date AS expected_pay_date,
    purchase_order.receival_date AS receival_date,
    purchase_order.confirm_date AS confirm_date,
    purchase_order.salesperson_name AS salesperson_name,
    purchase_order.freight AS freight,
    purchase_order.surcharge_value AS surcharge_value,
    purchase_order.discount_value AS discount_value,
    supplier_person.name AS supplier_name,
    transporter_person.name AS transporter_name,
    branch_person.name AS branch_name,
    sum(quantity) AS ordered_quantity,
    sum(quantity_received) AS received_quantity,
    sum(cost*quantity) AS subtotal,
    sum(cost*quantity) - purchase_order.discount_value + purchase_order.surcharge_value AS total

  FROM person_adapt_to_supplier,
       person AS supplier_person,
       person_adapt_to_branch,
       purchase_item,
       person AS branch_person,
       purchase_order
       
    LEFT JOIN person_adapt_to_transporter
    ON (purchase_order.transporter_id = person_adapt_to_transporter.id)

    LEFT JOIN person AS transporter_person
    ON (person_adapt_to_transporter.original_id = transporter_person.id)

  WHERE purchase_order.is_valid_model = 't' AND
        person_adapt_to_supplier.original_id = supplier_person.id AND
        person_adapt_to_branch.original_id = branch_person.id AND
        purchase_order.supplier_id = person_adapt_to_supplier.id AND
        purchase_order.branch_id = person_adapt_to_branch.id AND
        purchase_item.order_id = purchase_order.id

  GROUP BY purchase_item.order_id,
           purchase_order.id,
           purchase_order.status,
           purchase_order.order_number,
           purchase_order.open_date,
           purchase_order.quote_deadline,
           purchase_order.expected_receival_date,
           purchase_order.expected_pay_date,
           purchase_order.receival_date,
           purchase_order.confirm_date,
           purchase_order.salesperson_name,
           purchase_order.freight,
           purchase_order.surcharge_value,
           purchase_order.discount_value,
           supplier_person.name,
           transporter_person.name,
           branch_person.name

  HAVING order_id = purchase_order.id;

--
-- Stores information about clients.
-- Available fields are:
--    id                  - the id of the icms_ipi_book_entry table
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
-- Callsites:
--
--   stoqlib/gui/search/fiscalsearch.py
--
CREATE VIEW icms_ipi_view AS

  SELECT DISTINCT
    icms_ipi_book_entry.id AS id,
    icms_ipi_book_entry.icms_value AS icms_value,
    icms_ipi_book_entry.ipi_value AS ipi_value,
    abstract_fiscal_book_entry.date AS date,
    abstract_fiscal_book_entry.invoice_number AS invoice_number,
    abstract_fiscal_book_entry.cfop_id AS cfop_data_id,
    abstract_fiscal_book_entry.branch_id AS branch_id,
    abstract_fiscal_book_entry.drawee_id AS drawee_id,
    abstract_fiscal_book_entry.payment_group_id AS payment_group_id,
    cfop_data.code AS cfop_code,
    person.name AS drawee_name

  FROM cfop_data, icms_ipi_book_entry, abstract_fiscal_book_entry

   LEFT JOIN person
   ON (abstract_fiscal_book_entry.drawee_id = person.id)

  WHERE icms_ipi_book_entry.id = abstract_fiscal_book_entry.id AND 
        cfop_data.id = abstract_fiscal_book_entry.cfop_id;


--
-- Stores information about clients.
-- Available fields are:
--    id                  - the id of the iss_book_entry table
--    iss_value           - the total value of iss
--    date                - the date when the entry was created
--    invoice_number      - the invoice number
--    cfop_data_id        - the if of the cfop_data table
--    cfop_code           - the code of the cfop
--    drawee_name         - the drawee name
--    branch_id           - the id of the person_adapt_to_branch table
--    payment_group_id    - the if of the abstract_payment_group table
--
-- Callsites:
--
--   stoqlib/gui/search/fiscalsearch.py
--
CREATE VIEW iss_view AS

  SELECT DISTINCT
    iss_book_entry.id AS id,
    iss_book_entry.iss_value AS iss_value,
    abstract_fiscal_book_entry.date AS date,
    abstract_fiscal_book_entry.invoice_number AS invoice_number,
    abstract_fiscal_book_entry.cfop_id AS cfop_data_id,
    abstract_fiscal_book_entry.branch_id AS branch_id,
    abstract_fiscal_book_entry.drawee_id AS drawee_id,
    abstract_fiscal_book_entry.payment_group_id AS payment_group_id,
    cfop_data.code AS cfop_code,
    person.name AS drawee_name

  FROM iss_book_entry, cfop_data, abstract_fiscal_book_entry

    LEFT JOIN person
    ON (abstract_fiscal_book_entry.drawee_id = person.id)

  WHERE iss_book_entry.id = abstract_fiscal_book_entry.id AND
        cfop_data.id = abstract_fiscal_book_entry.cfop_id;


--
-- Stores information about payments
-- Available fields are:
--    identifier              - the identifier of till entries and payments
--    date                    - the date when the entry was created
--    description             - the entry description
--    value                   - the entry value
--    station_name            - the value of name branch_station name column
--
CREATE VIEW till_fiscal_operations_view AS

  SELECT DISTINCT
    payment.id AS id,
    payment.identifier AS identifier,
    payment.open_date AS date,
    payment.description AS description,
    payment.value AS value,
    branch_station.name AS station_name,
    person_adapt_to_branch.id AS branch_id,
    till.status AS status

  FROM payment, till, branch_station, person_adapt_to_branch

  WHERE payment.till_id = till.id AND
        till.station_id = branch_station.id AND
        branch_station.branch_id = person_adapt_to_branch.id;
