domain Package
==============

.. List of domain substitutions we are using, the current format is:
   For example, for the domain class SaleItem we have.
   Plural versions can also be added, they have an s in the end, but
   they still refer to the same domain class:
   * name of the link: sale item
   * name of the alias: |saleitem|
   * plural name of the link: sale items
   * plural name of the alias: |saleitems|
   Only add domain substitutions here.

.. |account| replace::
    :class:`account <stoqlib.domain.account.Account>`
.. |accounttransaction| replace::
    :class:`account transaction <stoqlib.domain.account.AccountTransaction>`
.. |accounttransactions| replace::
    :class:`account transactions <stoqlib.domain.account.AccountTransaction>`
.. |address| replace::
    :class:`address <stoqlib.domain.address.Address>`
.. |addresses| replace::
    :class:`addresses <stoqlib.domain.address.Address>`
.. |bankaccount| replace::
    :class:`bank account <stoqlib.domain.account.BankAccount>`
.. |branch| replace::
    :class:`branch <stoqlib.domain.person.Branch>`
.. |branches| replace::
    :class:`branches <stoqlib.domain.person.Branch>`
.. |branchstation| replace::
    :class:`branch station <stoqlib.domain.station.BranchStation>`
.. |client| replace::
    :class:`client <stoqlib.domain.person.Client>`
.. |clientcategory| replace::
    :class:`client category <stoqlib.domain.person.ClientCategory>`
.. |citylocation| replace::
    :class:`city location <CityLocation>`
.. |company| replace::
    :class:`company <stoqlib.domain.person.Company>`
.. |component| replace::
    :class:`component <stoqlib.domain.product.ProductComponent>`
.. |components| replace::
    :class:`components <stoqlib.domain.product.ProductComponent>`
.. |delivery| replace::
    :class:`delivery <stoqlib.domain.sale.Delivery>`
.. |employee| replace::
    :class:`employee <stoqlib.domain.person.Employee>`
.. |employees| replace::
    :class:`employees <stoqlib.domain.person.Employee>`
.. |individual| replace::
    :class:`individual <stoqlib.domain.person.Individual>`
.. |image| replace::
    :class:`image <stoqlib.domain.image.Image>`
.. |loan| replace::
    :class:`loan <stoqlib.domain.loan.Loan>`
.. |location| replace::
    :class:`location <stoqlib.domain.address.CityLocation>`
.. |loginuser| replace::
    :class:`login user <stoqlib.domain.person.LoginUser>`
.. |payment| replace::
    :class:`payment <stoqlib.domain.payment.payment.Payment>`
.. |paymentcategory| replace::
    :class:`category <stoqlib.domain.payment.category.PaymentCategory>`
.. |paymentgroup| replace::
    :class:`payment group <stoqlib.domain.payment.group.PaymentGroup>`
.. |paymentgroups| replace::
    :class:`payment groups <stoqlib.domain.payment.group.PaymentGroup>`
.. |paymentmethod| replace::
    :class:`payment method <stoqlib.domain.payment.method.PaymentMethod>`
.. |person| replace::
    :class:`person <stoqlib.domain.person.Person>`
.. |product| replace::
    :class:`product <stoqlib.domain.product.Product>`
.. |production| replace::
    :class:`production <stoqlib.domain.production.ProductionOrder>`
.. |purchase| replace::
    :class:`purchase <stoqlib.domain.purchase.PurchaseOrder>`
.. |receive| replace::
    :class:`receive <stoqlib.domain.receiving.ReceivingOrder>`
.. |returnedsale| replace::
    :class:`returned sale <stoqlib.domain.returnedsale.ReturnedSale>`
.. |sale| replace::
    :class:`sale <stoqlib.domain.sale.Sale>`
.. |saleitem| replace::
    :class:`sale item <stoqlib.domain.sale.SaleItem>`
.. |saleitems| replace::
    :class:`sale items <stoqlib.domain.sale.SaleItem>`
.. |salesperson| replace::
    :class:`salesperson <stoqlib.domain.person.SalesPerson>`
.. |sellable| replace::
    :class:`sellable <stoqlib.domain.sellable.Sellable>`
.. |sellablecategory| replace::
    :class:`sellable category <stoqlib.domain.sellable.SellableCategory>`
.. |sellabletaxconstant| replace::
    :class:`sellable tax constant <stoqlib.domain.sellable.SellableTaxConstant>`
.. |service| replace::
    :class:`service <stoqlib.domain.service.Service>`
.. |storable| replace::
    :class:`storable <stoqlib.domain.product.Storable>`
.. |supplier| replace::
    :class:`supplier <stoqlib.domain.person.Supplier>`
.. |suppliers| replace::
    :class:`suppliers <stoqlib.domain.person.Supplier>`
.. |transfer| replace::
    :class:`transfer <stoqlib.domain.transfer.TransferOrder>`
.. |transferitem| replace::
    :class:`transfer item <stoqlib.domain.transfer.TransferItem>`
.. |transferitems| replace::
    :class:`transfer items <stoqlib.domain.transfer.TransferItem>`
.. |till| replace::
    :class:`till <stoqlib.domain.till.Till>`
.. |tillentry| replace::
    :class:`till entry <stoqlib.domain.till.TillEntry>`
.. |transactionentry| replace::
    :class:`transaction entry <stoqlib.domain.system.TransactionEntry>`
.. |transporter| replace::
    :class:`transporter <stoqlib.domain.person.Transporter>`

:mod:`domain` Package
---------------------

.. automodule:: stoqlib.domain
    :members:
    :show-inheritance:

:mod:`account`
--------------

.. automodule:: stoqlib.domain.account
    :members:
    :show-inheritance:

:mod:`address`
--------------

.. automodule:: stoqlib.domain.address
    :members:
    :show-inheritance:

:mod:`base`
-----------

.. automodule:: stoqlib.domain.base
    :members:
    :show-inheritance:

:mod:`commission`
-----------------

.. automodule:: stoqlib.domain.commission
    :members:
    :show-inheritance:

:mod:`devices`
--------------

.. automodule:: stoqlib.domain.devices
    :members:
    :show-inheritance:

:mod:`event`
------------

.. automodule:: stoqlib.domain.event
    :members:
    :show-inheritance:

:mod:`events`
-------------

.. automodule:: stoqlib.domain.events
    :members:
    :show-inheritance:

:mod:`exampledata`
------------------

.. automodule:: stoqlib.domain.exampledata
    :members:
    :show-inheritance:

:mod:`fiscal`
-------------

.. automodule:: stoqlib.domain.fiscal
    :members:
    :show-inheritance:

:mod:`image`
------------

.. automodule:: stoqlib.domain.image
    :members:
    :show-inheritance:
    :exclude-members: on_create on_delete on_update

:mod:`interfaces`
-----------------

.. automodule:: stoqlib.domain.interfaces
    :members:
    :show-inheritance:

:mod:`inventory`
----------------

.. automodule:: stoqlib.domain.inventory
    :members:
    :show-inheritance:

:mod:`invoice`
--------------

.. automodule:: stoqlib.domain.invoice
    :members:
    :show-inheritance:

:mod:`loan`
-----------

.. automodule:: stoqlib.domain.loan
    :members:
    :show-inheritance:

:mod:`parameter`
----------------

.. automodule:: stoqlib.domain.parameter
    :members:
    :show-inheritance:

:mod:`payment.category`
-----------------------

.. automodule:: stoqlib.domain.payment.category
    :members:
    :show-inheritance:

:mod:`payment.comment`
----------------------

.. automodule:: stoqlib.domain.payment.comment
    :members:
    :show-inheritance:

:mod:`payment.group`
--------------------

.. automodule:: stoqlib.domain.payment.group
    :members:
    :show-inheritance:

:mod:`payment.method`
---------------------

.. automodule:: stoqlib.domain.payment.method
    :members:
    :show-inheritance:

:mod:`payment.operation`
------------------------

.. automodule:: stoqlib.domain.payment.operation
    :members:
    :show-inheritance:

:mod:`payment.payment`
----------------------

.. automodule:: stoqlib.domain.payment.payment
    :members:
    :show-inheritance:

:mod:`views`
------------

.. automodule:: stoqlib.domain.payment.views
    :members:
    :show-inheritance:


:mod:`person`
-------------

.. automodule:: stoqlib.domain.person
    :members:
    :show-inheritance:
    :exclude-members: on_create on_delete on_update

:mod:`plugin`
-------------

.. automodule:: stoqlib.domain.plugin
    :members:
    :show-inheritance:

:mod:`product`
--------------

.. automodule:: stoqlib.domain.product
    :members:
    :show-inheritance:
    :exclude-members: on_create on_delete on_update

:mod:`production`
-----------------

.. automodule:: stoqlib.domain.production
    :members:
    :show-inheritance:

:mod:`profile`
--------------

.. automodule:: stoqlib.domain.profile
    :members:
    :show-inheritance:

:mod:`purchase`
---------------

.. automodule:: stoqlib.domain.purchase
    :members:
    :show-inheritance:

:mod:`receiving`
----------------

.. automodule:: stoqlib.domain.receiving
    :members:
    :show-inheritance:

:mod:`returnedsale`
-------------------

.. automodule:: stoqlib.domain.returnedsale
    :members:
    :show-inheritance:

:mod:`sale`
-----------

.. automodule:: stoqlib.domain.sale
    :members:
    :show-inheritance:

:mod:`sellable`
---------------

.. automodule:: stoqlib.domain.sellable
    :members:
    :show-inheritance:
    :exclude-members: on_create on_delete on_update

:mod:`service`
--------------

.. automodule:: stoqlib.domain.service
    :members:
    :show-inheritance:
    :exclude-members: on_create on_delete on_update

:mod:`station`
--------------

.. automodule:: stoqlib.domain.station
    :members:
    :show-inheritance:
    :exclude-members: on_create on_delete on_update

:mod:`stockdecrease`
--------------------

.. automodule:: stoqlib.domain.stockdecrease
    :members:
    :show-inheritance:

:mod:`synchronization`
----------------------

.. automodule:: stoqlib.domain.synchronization
    :members:
    :show-inheritance:

:mod:`system`
-------------

.. automodule:: stoqlib.domain.system
    :members:
    :show-inheritance:

:mod:`taxes`
------------

.. automodule:: stoqlib.domain.taxes
    :members:
    :show-inheritance:

:mod:`till`
-----------

.. automodule:: stoqlib.domain.till
    :members:
    :show-inheritance:

:mod:`transfer`
---------------

.. automodule:: stoqlib.domain.transfer
    :members:
    :show-inheritance:

:mod:`uiform`
-------------

.. automodule:: stoqlib.domain.uiform
    :members:
    :show-inheritance:

:mod:`views`
------------

.. automodule:: stoqlib.domain.views
    :members:
    :show-inheritance:

Subpackages
-----------

.. toctree::

    stoqlib.domain.test

