Domain introduction
===================

FIXME: Write a quick introduction to the domain classes and how they fit into
the whole system. This is for beginners of Stoq.

The `domain classes <http://en.wikipedia.org/wiki/Domain_(software_engineering)>`__ contains the
business logic of Stoq.

The domain classes are written using the `Storm ORM <https://storm.canonical.com/>`__, the base class is Domain::

  >>> from stoqlib.domain.base import Domain
  >>>
  >>> class ExampleDomain(Domain):
  ...   __storm_table__ = 'example'

In the example above we import the Domain class which all domain classes
should inherit from. The only mandatory attribute is __storm_table__ which
defines which `database table <http://en.wikipedia.org/wiki/Table_(database)>`__ the domain table represent.

There is a 1 to 1 mapping between a database table and a domain class, there
must be exactly one table for one domain class.

Let's take a look at BranchStation which is a slightly longer domain class::

  >>> from stoqlib.domain.base import Domain
  >>> from stoqlib.database.properties import BoolCol, IntCol, Reference, UnicodeCol
  >>>
  >>> class BranchStation(Domain):
  ...    __storm_table__ = 'branch_station'
  ...
  ...    name = UnicodeCol()
  ...    branch_id = IntCol()
  ...    branch = Reference(branch_id, 'Branch.id')


The branch station database represents a computer that can be used a Stoq system.
It has two differente columns, the name of the station and the id branch_id.
The database schema for the **branch_station** table is defined as:

.. code-block:: sql

  CREATE TABLE branch_station (
      id serial NOT NULL PRIMARY KEY,
      name text UNIQUE,
      branch_id bigint REFERENCES branch(id) ON UPDATE CASCADE
  );

.. note:: the actual BranchStation domain class and the branch_station schema
  are a bit more complicated, we've simplied them here to make it easier to explain

To be able to explore the domain classes, use the **stoqdbadmin console** command that
allow you to use an interactive prompt to investigate the classes, assuming you
have `Stoq installed <devsetup>`__ you can type::

  $ stoqdbadmin console

And you will then be presented with a console such as::

  Stoq version 1.7.90, connected to stoq on :5432 (postgres)
  >>>

XXX: store & transactions
XXX: columns/fields
XXX: references

Overview
--------

The main domain classes of Stoq are:

  * Payment - transfer of money from one party to another
  * Product - an item that can be sold and stored
  * Purchase - aquisition of goods
  * Storable - physical location of a product
  * Sale - the exchange of goods for a profit

To figure out how the fit, let's use this simple table:

  +------------------+----------------------------------+
  | **Domain class** | **Application(s)**               |
  +------------------+----------------------------------+
  | Payment          | Accounts Payable & Receivable    |
  +------------------+----------------------------------+
  | Product          | Purchase, Production, Stock      |
  +------------------+----------------------------------+
  | Purchase         | Purchase                         |
  +------------------+----------------------------------+
  | Storable         | Inventory, Stock                 |
  +------------------+----------------------------------+
  | Sale             | Point of Sales, Sales, Till      |
  +------------------+----------------------------------+

Arguable the most important application of Stoq is the **Point of Sales** application,
which does the actual sales process in a quick and efficient way. Sales can however,
also be interacted with in other applications, most notable the **Sales** and **Till**.

Understanding a Sale
--------------------

When you complete a sale in P.O.S. you a new entry in the Sale table will be created.

This can be verified by using **stoqdbadmin console**::

  $ stoqdbadmin console

  >>> list(store.find(Sale))
  [<Sale 1>, <Sale 2>, <Sale 3>]
  >>> for sale in store.find(Sale):
  ...    print sale.id, sale.open_date, sale.total_amount
  ...
  1 2008-01-01 00:00:00 436.00
  2 2008-06-01 00:00:00 706.00
  3 2008-09-01 00:00:00 873.00

.. note:: As an exercise, create a new Payment in the Accounts Payable application and query for it using
   both psql and stoqdbadmin console

This can of course also be seen via **stoqdbadmin dbshell**::

  $ stoqdbadmin dbshell

.. code-block:: sql

  stoq=# SELECT id, open_date, total_amount FROM sale;
   id |      open_date      | total_amount
  ----+---------------------+--------------
    1 | 2008-01-01 00:00:00 |       436.00
    2 | 2008-06-01 00:00:00 |       706.00
    3 | 2008-09-01 00:00:00 |       873.00

In fact, if you run **stoqdbadmin console --sql** it will display all the SQL commands that were
executed, let's try that::

  $ stoqdbadmin console --sql

  Stoq version 1.7.90, connected to stoq on :5432 (postgres)
  >>> list(store.find(Sale))
  [29307     1] SELECT sale.branch_id, sale.cancel_date, sale.cfop_id, sale.client_category_id, sale.client_id, sale.close_date, sale.confirm_date,
                     sale.cost_center_id, sale.coupon_id, sale.discount_value, sale.expire_date, sale.group_id, sale.id, sale.identifier, sale.invoice_number,
                     sale.open_date, sale.operation_nature, sale.return_date, sale.salesperson_id, sale.service_invoice_number, sale.status,
                     sale.surcharge_value, sale.te_id, sale.total_amount, sale.transporter_id
              FROM sale
              0.107211 seconds | 3 rows
  [<Sale 1>, <Sale 2>, <Sale 3>]

You can see that when we typed store.find(Sale), a query is executed.

.. note:: Notice the usage of list() around the result from store.find(), that is required to force the query to be executed,
   as Storm ORM is lazy it will execute the queries unless they are needed!
