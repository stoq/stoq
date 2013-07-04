# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""
Domain objects related to the sale process in Stoq.

Sale object and related objects implementation """

from decimal import Decimal

from kiwi.currency import currency
from kiwi.python import Settable
from stoqdrivers.enum import TaxType
from storm.expr import (And, Avg, Count, LeftJoin, Join, Max,
                        Or, Sum, Alias, Select, Cast, Eq)
from storm.info import ClassAlias
from storm.references import Reference, ReferenceSet
from zope.interface import implements

from stoqlib.database.expr import Date, Field, TransactionTimestamp
from stoqlib.database.properties import (UnicodeCol, DateTimeCol, IntCol,
                                         PriceCol, QuantityCol, IdentifierCol,
                                         IdCol)
from stoqlib.database.runtime import (get_current_user,
                                      get_current_branch)
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.costcenter import CostCenter
from stoqlib.domain.event import Event
from stoqlib.domain.events import (SaleStatusChangedEvent,
                                   DeliveryStatusChangedEvent)
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.interfaces import IContainer, IPaymentTransaction
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import (Person, Client, Branch, LoginUser,
                                   SalesPerson)
from stoqlib.domain.product import (Product, ProductHistory, Storable,
                                    StockTransactionHistory)
from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.service import Service
from stoqlib.domain.taxes import SaleItemIcms, SaleItemIpi
from stoqlib.domain.till import Till
from stoqlib.exceptions import (SellError, StockError, DatabaseInconsistency,
                                StoqlibError)
from stoqlib.lib.component import Adaptable
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.defaults import quantize
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext

# pyflakes: Reference requires that CostCenter is imported at least once
CostCenter

#
# Base Domain Classes
#


class SaleItem(Domain):
    """An item of a |sellable| within a |sale|.

    Different from |sellable| which contains information about
    the base price, tax, etc, this contains the price in which
    *self* was sold, it's taxes, the quantity, etc.

    Note that objects of this type should never be created manually, only by
    calling :meth:`Sale.add_sellable`

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/sale_item.html>`__
    """

    __storm_table__ = 'sale_item'

    #: the quantity of the of sold item in this sale
    quantity = QuantityCol()

    #: the quantity already decreased from stock.
    quantity_decreased = QuantityCol(default=0)

    #: original value the |sellable| had when adding the sale item
    base_price = PriceCol()

    #: averiage cost of the items in this item
    average_cost = PriceCol(default=0)

    #: price of this item
    price = PriceCol()

    sale_id = IdCol()

    #: |sale| for this item
    sale = Reference(sale_id, 'Sale.id')

    sellable_id = IdCol()

    #: |sellable| for this item
    sellable = Reference(sellable_id, 'Sellable.id')

    batch_id = IdCol()

    #: If the sellable is a storable, the |batch| that it was removed from
    batch = Reference(batch_id, 'StorableBatch.id')

    delivery_id = IdCol(default=None)

    #: |delivery| or None
    delivery = Reference(delivery_id, 'Delivery.id')

    cfop_id = IdCol(default=None)

    #: :class:`fiscal entry <stoqlib.domain.fiscal.CfopData>`
    cfop = Reference(cfop_id, 'CfopData.id')

    #: user defined notes, currently only used by services
    notes = UnicodeCol(default=None)

    #: estimated date that *self* will be fixed, currently
    #: only used by services
    estimated_fix_date = DateTimeCol(default_factory=localnow)

    # FIXME: This doesn't appear to be used anywhere. Maybe we
    #        should remove it from the database
    completion_date = DateTimeCol(default=None)

    icms_info_id = IdCol()

    #: the :class:`stoqlib.domain.taxes.SaleItemIcms` tax for *self*
    icms_info = Reference(icms_info_id, 'SaleItemIcms.id')

    ipi_info_id = IdCol()

    #: the :class:`stoqlib.domain.taxes.SaleItemIpi` tax for *self*
    ipi_info = Reference(ipi_info_id, 'SaleItemIpi.id')

    def __init__(self, store=None, **kw):
        if not 'kw' in kw:
            if not 'sellable' in kw:
                raise TypeError('You must provide a sellable argument')
            base_price = kw['sellable'].price
            kw['base_price'] = base_price
            if not kw.get('cfop'):
                kw['cfop'] = kw['sellable'].default_sale_cfop
            if not kw.get('cfop'):
                kw['cfop'] = sysparam(store).DEFAULT_SALES_CFOP

            store = kw.get('store', store)
            kw['ipi_info'] = SaleItemIpi(store=store)
            kw['icms_info'] = SaleItemIcms(store=store)
        Domain.__init__(self, store=store, **kw)

        product = self.sellable.product
        if product:
            # Set ipi details before icms, since icms may depend on the ipi
            self.ipi_info.set_from_template(self.sellable.product.ipi_template)
            self.icms_info.set_from_template(self.sellable.product.icms_template)

    #
    #  Public API
    #

    @property
    def returned_quantity(self):
        return self.store.find(ReturnedSaleItem,
                               sale_item=self).sum(ReturnedSaleItem.quantity) or Decimal('0')

    def sell(self, branch):
        store = self.store
        if not (branch and
                branch.id == get_current_branch(store).id):
            raise SellError(_(u"Stoq still doesn't support sales for "
                              u"branch companies different than the "
                              u"current one"))

        if not self.sellable.is_available():
            raise SellError(_(u"%s is not available for sale. Try making it "
                              u"available first and then try again.") % (
                self.sellable.get_description()))

        quantity_to_decrease = self.quantity - self.quantity_decreased
        storable = self.sellable.product_storable
        if storable and quantity_to_decrease:
            try:
                item = storable.decrease_stock(
                    quantity_to_decrease, branch,
                    StockTransactionHistory.TYPE_SELL, self.id,
                    cost_center=self.sale.cost_center, batch=self.batch)
            except StockError as err:
                raise SellError(str(err))

            self.average_cost = item.stock_cost
            self.quantity_decreased += quantity_to_decrease

    def cancel(self, branch):
        storable = self.sellable.product_storable
        if storable and self.quantity_decreased:
            storable.increase_stock(self.quantity_decreased,
                                    branch,
                                    StockTransactionHistory.TYPE_CANCELED_SALE,
                                    self.id,
                                    batch=self.batch)
            self.quantity_decreased = Decimal(0)

    def get_total(self):
        # Sale items are suposed to have only 2 digits, but the value price
        # * quantity may have more than 2, so we need to round it.
        if self.ipi_info:
            return currency(quantize(self.price * self.quantity +
                                     self.ipi_info.v_ipi))
        return currency(quantize(self.price * self.quantity))

    def get_quantity_unit_string(self):
        return u"%s %s" % (self.quantity, self.sellable.get_unit_description())

    def get_description(self):
        return self.sellable.get_description()

    def is_totally_returned(self):
        """If this sale item was totally returned

        :returns: ``True`` if it was totally returned,
            ``False`` otherwise.
        """
        return self.quantity == self.returned_quantity

    def is_service(self):
        """If this sale item contains a |service|.

        :returns: ``True`` if it's a service
        """
        service = self.store.find(Service, sellable=self.sellable).one()
        return service is not None

    def get_nfe_icms_info(self):
        """ICMS details to be used on the NF-e

        If the sale was also printed on a coupon, then we cannot add icms
        details to the NF-e (or at least, we should modify then accordingly)

        :returns: the :class:`icms info <stoqlib.domain.taxes.SaleItemIcms>`
            or *None*, if a coupon has been printed for this Sale
        """
        if self.sale.coupon_id:
            return None

        return self.icms_info

    def get_nfe_ipi_info(self):
        """IPI details for this SaleItem

        :returns: the :class:`ipi info <stoqlib.domain.taxes.SaleItemIpip>`
        """
        return self.ipi_info

    def get_nfe_cfop_code(self):
        """Returns the cfop code to be used on the NF-e

        If the sale was also printed on a ECF, then the cfop should be:
          * 5.929: if sold to a |Client| in the same state or
          * 6-929: if sold to a |Client| in a different state.

        :returns: the cfop code
        """
        if self.sale.coupon_id:
            # find out if the client is in the same state as we are.
            client_address = self.sale.client.person.get_main_address()
            our_address = self.sale.branch.person.get_main_address()

            same_state = True
            if (our_address.city_location.state !=
                client_address.city_location.state):
                same_state = False

            if same_state:
                return u'5929'
            else:
                return u'6929'

        if self.cfop:
            return self.cfop.code.replace(u'.', u'')

        # FIXME: remove sale cfop?
        return self.sale.cfop.code.replace(u'.', u'')

    def get_sale_discount(self):
        """The discount percentage (relative to the original price
           when the item was sold)

        :returns: the discount amount
        """
        if self.price > 0 and self.price < self.base_price:
            return (1 - (self.price / self.base_price)) * 100
        return 0

    def get_sale_surcharge(self):
        """The surcharge percentage (relative to the original price
           when the item was sold)

        :returns: the surcharge amount
        """
        if self.price > self.base_price:
            return ((self.price / self.base_price) - 1) * 100
        return 0


class Delivery(Domain):
    """Delivery, transporting a set of sale items for sale.

    Involves a |transporter| transporting a set of |saleitems| to a
    receival |address|.

    Optionally a :obj:`.tracking_code` can be set to track the items.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/delivery.html>`__
    """

    implements(IContainer)

    __storm_table__ = 'delivery'

    #: The delivery was created
    STATUS_INITIAL = 0

    #: sent to deliver
    STATUS_SENT = 1

    #: received by the |client|
    STATUS_RECEIVED = 2

    statuses = {STATUS_INITIAL: _(u"Waiting"),
                STATUS_SENT: _(u"Sent"),
                STATUS_RECEIVED: _(u"Received")}

    #: the delivery status
    status = IntCol(default=STATUS_INITIAL)

    #: the date which the delivery was created
    open_date = DateTimeCol(default=None)

    #: the date which the delivery sent to deliver
    deliver_date = DateTimeCol(default=None)

    #: the date which the delivery received by the |client|
    receive_date = DateTimeCol(default=None)

    #: the delivery tracking code, a transporter specific identifier that
    #: can be used to look up the status of the delivery
    tracking_code = UnicodeCol(default=u'')

    address_id = IdCol(default=None)

    #: the |address| to deliver to
    address = Reference(address_id, 'Address.id')

    transporter_id = IdCol(default=None)

    #: the |transporter| for this delivery
    transporter = Reference(transporter_id, 'Transporter.id')

    service_item_id = IdCol(default=None)

    #: the |saleitem| for the delivery itself
    service_item = Reference(service_item_id, 'SaleItem.id')

    #: the |saleitems| for the items to deliver
    delivery_items = ReferenceSet('id', 'SaleItem.delivery_id')

    def __init__(self, store=None, **kwargs):
        if not 'open_date' in kwargs:
            kwargs['open_date'] = TransactionTimestamp()

        super(Delivery, self).__init__(store=store, **kwargs)

    #
    #  Properties
    #

    @property
    def status_str(self):
        return self.statuses[self.status]

    @property
    def address_str(self):
        if self.address:
            return self.address.get_address_string()
        return u''

    @property
    def client_str(self):
        client = self.service_item.sale.client
        if client:
            return client.get_description()
        return u''

    #
    #  Public API
    #

    def set_initial(self):
        self._set_delivery_status(self.STATUS_INITIAL)

    def set_sent(self):
        self._set_delivery_status(self.STATUS_SENT)

    def set_received(self):
        self._set_delivery_status(self.STATUS_RECEIVED)

    #
    #  IContainer implementation
    #

    def add_item(self, item):
        item.delivery = self

    def get_items(self):
        return list(self.delivery_items)

    def remove_item(self, item):
        item.delivery = None

    #
    #  Private
    #

    def _set_delivery_status(self, status):
        old_status = self.status
        DeliveryStatusChangedEvent.emit(self, old_status)
        self.status = status


class Sale(Domain, Adaptable):
    """Sale logic, the process of selling a |sellable| to a |client|.

    A large part of the payment processing logic is done via
    the :class:`SaleAdaptToPaymentTransaction` adapter.

    * calculates the sale price including discount/interest/markup
    * creates payments
    * decreases the stock for products
    * creates a delivery (optional)
    * verifies that the client is suitable
    * creates commissions to the sales person
    * add money to the till (if paid with money)
    * calculate taxes and fiscal book entries

    +----------------------------+----------------------------+
    | **Status**                 | **Can be set to**          |
    +----------------------------+----------------------------+
    | :obj:`STATUS_QUOTE`        | :obj:`STATUS_INITIAL`      |
    +----------------------------+----------------------------+
    | :obj:`STATUS_INITIAL`      | :obj:`STATUS_ORDERED`,     |
    +----------------------------+----------------------------+
    | :obj:`STATUS_ORDERED`      | :obj:`STATUS_PAID`,        |
    |                            | :obj:`STATUS_CONFIRMED`    |
    |                            | :obj:`STATUS_CANCELLED`    |
    +----------------------------+----------------------------+
    | :obj:`STATUS_CONFIRMED`    | :obj:`STATUS_PAID`         |
    |                            | :obj:`STATUS_RENEGOTIATED` |
    +----------------------------+----------------------------+
    | :obj:`STATUS_CANCELLED`    | None                       |
    +----------------------------+----------------------------+
    | :obj:`STATUS_PAID`         | None                       |
    +----------------------------+----------------------------+
    | :obj:`STATUS_RENEGOTIATED` | None                       |
    +----------------------------+----------------------------+
    | :obj:`STATUS_RETURNED`     | None                       |
    +----------------------------+----------------------------+

    .. graphviz::

       digraph sale_status {
         STATUS_QUOTE -> STATUS_INITIAL;
         STATUS_INITIAL -> STATUS_ORDERED;
         STATUS_ORDERED -> STATUS_PAID;
         STATUS_ORDERED -> STATUS_CONFIRMED;
         STATUS_ORDERED -> STATUS_CANCELLED;
         STATUS_CONFIRMED -> STATUS_PAID;
         STATUS_CONFIRMED -> STATUS_CANCELLED;
         STATUS_PAID -> STATUS_RETURNED;
         STATUS_CONFIRMED -> STATUS_RENEGOTIATED;
       }

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/sale.html>`__
    """

    implements(IContainer)

    __storm_table__ = 'sale'

    #: The sale is opened, products or other |sellable| items might have
    #: been added.
    STATUS_INITIAL = 0

    #: The sale has been confirmed and all payments have been registered,
    #: but not necessarily paid.
    STATUS_CONFIRMED = 1

    #: All the payments of the sale has been confirmed and the |client| does
    #: not owe anything to us. The product stock has been decreased and the
    #: items delivered.
    STATUS_PAID = 2

    #: The sale has been canceled, this can only happen
    #: to an sale which has not yet reached the SALE_CONFIRMED status.
    STATUS_CANCELLED = 3

    #: The sale is orded, it has sellable items but not any payments yet.
    #: This state is mainly used when the parameter CONFIRM_SALES_AT_TILL
    #: is enabled.
    STATUS_ORDERED = 4

    #: The sale has been returned, all the payments made have been canceled
    #: and the |client| has been compensated for everything already paid.
    STATUS_RETURNED = 5

    #: When asking for sale quote this is the initial state that is set before
    #: reaching the initial state
    STATUS_QUOTE = 6

    #: A sale that is closed as renegotiated, all payments for this sale
    #: should be canceled at list point. Another new sale is created with
    #: the new, renegotiated payments.
    STATUS_RENEGOTIATED = 7

    statuses = {STATUS_INITIAL: _(u'Opened'),
                STATUS_CONFIRMED: _(u'Confirmed'),
                STATUS_PAID: _(u'Paid'),
                STATUS_CANCELLED: _(u'Cancelled'),
                STATUS_ORDERED: _(u'Ordered'),
                STATUS_RETURNED: _(u'Returned'),
                STATUS_RENEGOTIATED: _(u'Renegotiated'),
                STATUS_QUOTE: _(u'Quoting')}

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: status of the sale
    status = IntCol(default=STATUS_INITIAL)

    # FIXME: this doesn't really belong to the sale
    # FIXME: it should also be renamed and avoid *_id
    #: identifier for the coupon of this sale, used by a ECF printer
    coupon_id = IntCol()

    # FIXME: This doesn't appear to be used anywhere.
    #        Maybe we should remove it from the database.
    service_invoice_number = IntCol(default=None)

    #: Some optional additional information related to this sale.
    notes = UnicodeCol(default=u'')

    #: the date sale was created, this is always set
    open_date = DateTimeCol(default_factory=localnow)

    #: the date sale was confirmed, or None if it hasn't been confirmed
    confirm_date = DateTimeCol(default=None)

    #: the date sale was paid, or None if it hasn't be paid
    close_date = DateTimeCol(default=None)

    #: the date sale was confirmed, or None if it hasn't been cancelled
    cancel_date = DateTimeCol(default=None)

    #: the date sale was confirmed, or None if it hasn't been returned
    return_date = DateTimeCol(default=None)

    #: date when this sale expires, used by quotes
    expire_date = DateTimeCol(default=None)

    #: discount of the sale, in absolute value, for instance::
    #:
    #:    sale.total_sale_amount = 150
    #:    sale.discount_value = 18
    #:    # the price of the sale will now be 132
    #:
    discount_value = PriceCol(default=0)

    #: surcharge of the sale, in absolute value, for instance::
    #:
    #:    sale.total_sale_amount = 150
    #:    sale.surcharge_value = 18
    #:    # the price of the sale will now be 168
    #:
    surcharge_value = PriceCol(default=0)

    #: the total value of all the items in the same, this is set when
    #: a sale is confirmed, this is the same as calling
    #: :obj:`Sale.get_total_sale_amount()` at the time of confirming the sale,
    total_amount = PriceCol(default=0)

    #: invoice number for this sale, appears on bills etc.
    invoice_number = IntCol(default=None)
    operation_nature = UnicodeCol(default=u'')

    cfop_id = IdCol()

    #: the :class:`fiscal entry <stoqlib.domain.fiscal.CfopData>`
    cfop = Reference(cfop_id, 'CfopData.id')

    client_id = IdCol(default=None)

    #: the |client| who this sale was sold to
    client = Reference(client_id, 'Client.id')

    salesperson_id = IdCol()

    #: the |salesperson| who sold the sale
    salesperson = Reference(salesperson_id, 'SalesPerson.id')

    branch_id = IdCol()

    #: the |branch| this sale belongs to
    branch = Reference(branch_id, 'Branch.id')

    transporter_id = IdCol(default=None)

    # FIXME: transporter should only be used on Delivery.
    #: If we have a delivery, this is the |transporter| for this sale
    transporter = Reference(transporter_id, 'Transporter.id')

    group_id = IdCol()

    #: the |paymentgroup| of this sale
    group = Reference(group_id, 'PaymentGroup.id')

    client_category_id = IdCol(default=None)

    #: the |clientcategory| used for price determination.
    client_category = Reference(client_category_id, 'ClientCategory.id')

    cost_center_id = IdCol(default=None)

    #: the |costcenter| that the cost of the products sold in this sale should
    #: be accounted for. When confirming a sale with a |costcenter| set, a
    #: |costcenterentry| will be created for each product
    cost_center = Reference(cost_center_id, 'CostCenter.id')

    def __init__(self, store=None, **kw):
        super(Sale, self).__init__(store=store, **kw)
        # Branch needs to be set before cfop, which triggers an
        # implicit flush.
        self.branch = kw.pop('branch', None)
        if not 'cfop' in kw:
            self.cfop = sysparam(store).DEFAULT_SALES_CFOP
        self.addFacet(IPaymentTransaction)

    def __storm_loaded__(self):
        super(Sale, self).__storm_loaded__()
        self.addFacet(IPaymentTransaction)

    #
    # Classmethods
    #

    @classmethod
    def get_status_name(cls, status):
        """The :obj:`Sale.status` as a translated string"""
        if not status in cls.statuses:
            raise DatabaseInconsistency(_(u"Invalid status %d") % status)
        return cls.statuses[status]

    @classmethod
    def get_last_invoice_number(cls, store):
        """Returns the last sale invoice number. If there is not an invoice
        number used, the returned value will be zero.

        :param store: a store
        :returns: an integer representing the last sale invoice number
        """
        return store.find(cls).max(cls.invoice_number) or 0

    #
    # IContainer implementation
    #

    def add_item(self, sale_item):
        assert not sale_item.sale
        sale_item.sale = self

    def get_items(self):
        store = self.store
        return store.find(SaleItem, sale=self)

    def remove_item(self, sale_item):
        self.store.remove(sale_item)

    # Status

    def can_order(self):
        """Only newly created sales can be ordered

        :returns: ``True`` if the sale can be ordered
        """
        return (self.status == Sale.STATUS_INITIAL or
                self.status == Sale.STATUS_QUOTE)

    def can_confirm(self):
        """Only ordered sales can be confirmed

        :returns: ``True`` if the sale can be confirmed
        """
        if self.client:
            method_values = {}
            for p in self.payments:
                method_values.setdefault(p.method, 0)
                method_values[p.method] += p.value
            for method, value in method_values.items():
                assert self.client.can_purchase(method, value)

        return (self.status == Sale.STATUS_ORDERED or
                self.status == Sale.STATUS_QUOTE)

    def can_set_paid(self):
        """Only confirmed sales can be paid. Also, the sale must have at least
        one payment and all the payments must be already paid.

        :returns: ``True`` if the sale can be set as paid
        """
        if self.status != Sale.STATUS_CONFIRMED:
            return False

        payments = list(self.payments)
        if not payments:
            return False

        return all(p.is_paid() for p in payments)

    def can_set_not_paid(self):
        """Only confirmed sales can be paid

        :returns: ``True`` if the sale can be set as paid
        """
        return self.status == Sale.STATUS_PAID

    def can_set_renegotiated(self):
        """Only sales with status confirmed can be renegotiated.

        :returns: ``True`` if the sale can be renegotiated
        """
        # This should be as simple as:
        # return self.status == Sale.STATUS_CONFIRMED
        # But due to bug 3890 we have to check every payment.
        return self.payments.find(
            Payment.status == Payment.STATUS_PENDING).count() > 0

    def can_cancel(self):
        """Only ordered, confirmed, paid and quoting sales can be cancelled.

        :returns: ``True`` if the sale can be cancelled
        """
        return self.status in (Sale.STATUS_CONFIRMED, Sale.STATUS_PAID,
                               Sale.STATUS_ORDERED, Sale.STATUS_QUOTE)

    def can_return(self):
        """Only confirmed or paid sales can be returned

        :returns: ``True`` if the sale can be returned
        """
        return (self.status == Sale.STATUS_CONFIRMED or
                self.status == Sale.STATUS_PAID)

    def can_edit(self):
        """Only quoting sales can be edited.

        :returns: ``True`` if the sale can be edited
        """
        return self.status == Sale.STATUS_QUOTE

    def order(self):
        """Orders the sale

        Ordering a sale is the first step done after creating it.
        The state of the sale will change to Sale.STATUS_ORDERED.
        To order a sale you need to add sale items to it.
        A |client| might also be set for the sale, but it is not necessary.
        """
        assert self.can_order()
        if self.get_items().is_empty():
            raise SellError(_('The sale must have sellable items'))
        if self.client and not self.client.is_active:
            raise SellError(_('Unable to make sales for clients with status '
                              '%s') % self.client.get_status_string())

        self._set_sale_status(Sale.STATUS_ORDERED)

    def confirm(self):
        """Confirms the sale

        Confirming a sale means that the customer has confirmed the sale.
        Sale items containing products are physically received and
        the payments are agreed upon but not necessarily received.

        All money payments will be set as paid.
        """
        assert self.can_confirm()
        assert self.branch

        # FIXME: We should use self.branch, but it's not supported yet
        store = self.store
        branch = get_current_branch(store)
        for item in self.get_items():
            self.validate_batch(item.batch, sellable=item.sellable)
            if item.sellable.product:
                ProductHistory.add_sold_item(store, branch, item)
            item.sell(branch)

        self.total_amount = self.get_total_sale_amount()

        transaction = IPaymentTransaction(self)
        transaction.confirm()

        if self.client:
            self.group.payer = self.client.person

        self.confirm_date = TransactionTimestamp()
        self._set_sale_status(Sale.STATUS_CONFIRMED)

        # When confirming a sale, all credit and money payments are
        # automatically paid.
        for method in (u'money', u'credit'):
            self.group.pay_method_payments(method)

        # do not log money payments twice
        if not self.only_paid_with_money():
            if self.client:
                msg = _(u"Sale {sale_number} to client {client_name} was "
                        u"confirmed with value {total_value:.2f}.").format(
                    sale_number=self.identifier,
                    client_name=self.client.person.name,
                    total_value=self.get_total_sale_amount())
            else:
                msg = _(u"Sale {sale_number} without a client was "
                        u"confirmed with value {total_value:.2f}.").format(
                    sale_number=self.identifier,
                    total_value=self.get_total_sale_amount())
            Event.log(self.store, Event.TYPE_SALE, msg)

    def set_paid(self):
        """Mark the sale as paid
        Marking a sale as paid means that all the payments have been received.
        """
        assert self.can_set_paid()

        for payment in self.payments:
            if not payment.is_paid():
                raise StoqlibError(
                    _(u"You cannot close a sale without paying all the payment. "
                      u"Payment %r is still not paid") % (payment, ))

        transaction = IPaymentTransaction(self)
        transaction.pay()

        self.close_date = TransactionTimestamp()
        self._set_sale_status(Sale.STATUS_PAID)

        if self.only_paid_with_money():
            # Money payments are confirmed and paid, so lof them that way
            if self.client:
                msg = _(u"Sale {sale_number} to client {client_name} was paid "
                        u"and confirmed with value {total_value:.2f}.").format(
                    sale_number=self.identifier,
                    client_name=self.client.person.name,
                    total_value=self.get_total_sale_amount())
            else:
                msg = _(u"Sale {sale_number} without a client was paid "
                        u"and confirmed with value {total_value:.2f}.").format(
                    sale_number=self.identifier,
                    total_value=self.get_total_sale_amount())
        else:
            if self.client:
                msg = _(u"Sale {sale_number} to client {client_name} was paid "
                        u"with value {total_value:.2f}.").format(
                    sale_number=self.identifier,
                    client_name=self.client.person.name,
                    total_value=self.get_total_sale_amount())
            else:
                msg = _(u"Sale {sale_number} without a client was paid "
                        u"with value {total_value:.2f}.").format(
                    sale_number=self.identifier,
                    total_value=self.get_total_sale_amount())
        Event.log(self.store, Event.TYPE_SALE, msg)

    def set_not_paid(self):
        """Mark a sale as not paid. This happens when the user sets a
        previously paid payment as not paid.

        In this case, if the sale status is :obj:`.STATUS_PAID`,
        it should be set back to :obj:`.STATUS_CONFIRMED`.
        """
        assert self.can_set_not_paid()

        self.close_date = None
        self._set_sale_status(Sale.STATUS_CONFIRMED)

    def set_renegotiated(self):
        """Set the sale as renegotiated. The sale payments have been
        renegotiated and the operations will be done in
        another |paymentgroup|."""
        assert self.can_set_renegotiated()

        self.close_date = TransactionTimestamp()
        self._set_sale_status(Sale.STATUS_RENEGOTIATED)

    def cancel(self):
        """Cancel the sale
        You can only cancel an ordered sale.
        This does not cancel the payments, only the sale items.
        """
        assert self.can_cancel()

        branch = get_current_branch(self.store)
        for item in self.get_items():
            item.cancel(branch)

        self.cancel_date = TransactionTimestamp()
        self._set_sale_status(Sale.STATUS_CANCELLED)

    def return_(self, returned_sale):
        """Returns a sale
        Returning a sale means that all the items are returned to the stock.
        A renegotiation object needs to be supplied which
        contains the invoice number and the eventual penalty

        :param returned_sale: a :class:`stoqlib.domain.returnedsale.ReturnedSale`
            object. It can be created by :meth:`create_sale_return_adapter`
        """
        assert self.can_return()
        assert isinstance(returned_sale, ReturnedSale)

        totally_returned = all([sale_item.is_totally_returned() for
                                sale_item in self.get_items()])
        if totally_returned:
            self.return_date = TransactionTimestamp()
            self._set_sale_status(Sale.STATUS_RETURNED)

        transaction = IPaymentTransaction(self)
        transaction.return_(returned_sale)

        if self.client:
            if totally_returned:
                msg = _(u"Sale {sale_number} to client {client_name} was "
                        u"totally returned with value {total_value:.2f}. "
                        u"Reason: {reason}")
            else:
                msg = _(u"Sale {sale_number} to client {client_name} was "
                        u"partially returned with value {total_value:.2f}. "
                        u"Reason: {reason}")
            msg = msg.format(sale_number=self.identifier,
                             client_name=self.client.person.name,
                             total_value=returned_sale.returned_total,
                             reason=returned_sale.reason)
        else:
            if totally_returned:
                msg = _(u"Sale {sale_number} without a client was "
                        u"totally returned with value {total_value:.2f}. "
                        u"Reason: {reason}")
            else:
                msg = _(u"Sale {sale_number} without a client was "
                        u"partially returned with value {total_value:.2f}. "
                        u"Reason: {reason}")
            msg = msg.format(sale_number=self.identifier,
                             total_value=returned_sale.returned_total,
                             reason=returned_sale.reason)

        Event.log(self.store, Event.TYPE_SALE, msg)

    #
    # Accessors
    #

    def get_total_sale_amount(self, subtotal=None):
        """
        Fetches the total value  paid by the |client|.
        It can be calculated as::

            Sale total = Sum(product and service prices) + surcharge +
                             interest - discount

        :param subtotal: pre calculated subtotal, pass in this to avoid
           a querying the database
        :returns: the total value
        """

        if subtotal is None:
            subtotal = self.get_sale_subtotal()

        surcharge_value = self.surcharge_value or Decimal(0)
        discount_value = self.discount_value or Decimal(0)
        total_amount = subtotal + surcharge_value - discount_value
        return currency(total_amount)

    def get_sale_subtotal(self):
        """Fetch the subtotal for the sale, eg the sum of the
        prices for of all items.

        :returns: subtotal
        """
        total = 0
        for i in self.get_items():
            total += i.get_total()

        return currency(total)

    def get_items_total_quantity(self):
        """Fetches the total number of items in the sale

        :returns: number of items
        """
        return self.get_items().sum(SaleItem.quantity) or Decimal(0)

    def get_total_paid(self):
        """Return the total amount already paid for this sale
        :returns: the total amount paid
        """
        total_paid = 0
        for payment in self.group.get_valid_payments():
            if payment.is_inpayment() and payment.is_paid():
                # Already paid by client. Value instead of paid_value as the
                # second might have penalties and discounts not applicable here
                total_paid += payment.value
            elif payment.is_outpayment():
                # Already returned to client
                total_paid -= payment.value

        return currency(total_paid)

    def get_total_to_pay(self):
        """Missing payment value for this sale.

        Returns the value the client still needs to pay for this sale.
        This is the same as
        :meth:`.get_total_sale_amount` - :meth:`.get_total_paid`
        """
        return currency(self.get_total_sale_amount() - self.get_total_paid())

    def get_details_str(self):
        """Returns the sale details. The details are composed by the sale
        notes, the items notes, the delivery address and the estimated fix
        date.

        :returns: the sale details string.
        """
        details = []
        if self.notes:
            details.append(_(u'Sale Details: %s') % self.notes)
        delivery_added = False
        for sale_item in self.get_items():
            if delivery_added is False:
                # FIXME: Add the delivery info just once can lead to an error.
                #        It's possible that some item went to delivery X while
                #        some went to delivery Y.
                delivery = sale_item.delivery
            if delivery is not None:
                details.append(_(u'Delivery Address: %s') %
                               delivery.address.get_address_string())
                # At the moment, we just support only one delivery per sale.
                delivery_added = True
                delivery = None
            else:
                if sale_item.notes:
                    details.append(_(u'"%s" Notes: %s') % (
                        sale_item.get_description(), sale_item.notes))
            if sale_item.is_service() and sale_item.estimated_fix_date:
                details.append(_(u'"%s" Estimated Fix Date: %s') % (
                    sale_item.get_description(),
                    sale_item.estimated_fix_date.strftime('%x')))
        return u'\n'.join(details)

    def get_salesperson_name(self):
        """
        :returns: the sales person name
        """
        return self.salesperson.get_description()

    def get_client_name(self):
        """Returns the client name, if a |client| has been provided for
        this sale

        :returns: the client name of a place holder string for sales without
           clients set.
        """
        if not self.client:
            return _(u'Not Specified')
        return self.client.get_name()

    # FIXME: move over to client or person
    def get_client_role(self):
        """Fetches the client role

        :returns: the client role (an |individual| or a |company|) instance or
          None if the sale haven't |client| set.
        """
        if not self.client:
            return None
        client_role = self.client.person.has_individual_or_company_facets()
        if client_role is None:
            raise DatabaseInconsistency(
                _(u"The sale %r have a client but no "
                  u"client_role defined.") % self)

        return client_role

    def get_items_missing_batch(self):
        """Get all |saleitems| missing |batch|

        This usually happens when we create a quote. Since we are
        not removing the items from the stock, they probably were
        not set on the |saleitem|.

        :returns: a result set of |saleitems| that needs to set
            set the batch information
        """
        return self.store.find(
            SaleItem,
            And(SaleItem.sale_id == self.id,
                SaleItem.sellable_id == Sellable.id,
                Product.sellable_id == Sellable.id,
                Storable.product_id == Product.id,
                Eq(Storable.is_batch, True),
                Eq(SaleItem.batch_id, None)))

    def need_adjust_batches(self):
        """Checks if we need to set |batches| for this sale's |saleitems|

        This usually happens when we create a quote. Since we are
        not removing the items from the stock, they probably were
        not set on the |saleitem|.

        :returns: ``True`` if any |saleitem| needs a |batch|,
            ``False`` otherwise.
        """
        return not self.get_items_missing_batch().is_empty()

    def only_paid_with_money(self):
        """Find out if the sale is paid using money

        :returns: ``True`` if the sale was paid with money
        """
        if self.payments.is_empty():
            return False
        return all(payment.is_of_method(u'money') for payment in self.payments)

    def add_sellable(self, sellable, quantity=1, price=None,
                     quantity_decreased=0, batch=None):
        """Adds a new item to a sale.

        :param sellable: the |sellable|
        :param quantity: quantity to add, defaults to 1
        :param price: optional, the price, it not set the price
          from the sellable will be used
        :param quantity_decreased: the quantity already decreased from
          stock. e.g. The param quantity 10 and that quantity were already
          decreased, so this param should be 10 too.
        :param batch: the |batch| this sellable comes from, if the sellable is a
          storable. Should be ``None`` if it is not a storable or if the storable
          does not have batches.
        :returns: a |saleitem| for representing the
          sellable within this sale.
        """
        # Quote can add items without batches, but they will be validated
        # after on self.confirm
        if self.status != self.STATUS_QUOTE:
            self.validate_batch(batch, sellable=sellable)
        price = price or sellable.price
        return SaleItem(store=self.store,
                        quantity=quantity,
                        quantity_decreased=quantity_decreased,
                        sale=self,
                        sellable=sellable,
                        batch=batch,
                        price=price)

    def create_sale_return_adapter(self):
        store = self.store
        current_user = get_current_user(store)
        returned_sale = ReturnedSale(
            store=store,
            sale=self,
            branch=get_current_branch(store),
            responsible=current_user,
        )
        for sale_item in self.get_items():
            if sale_item.is_totally_returned():
                # Exclude quantities already returned from this one
                continue
            # If sale_item is a product, use the quantity that was decreased
            # to return. If a service, use quantity directly since services
            # doesn't change stock.
            if sale_item.sellable.product_storable:
                quantity = sale_item.quantity_decreased
            else:
                quantity = sale_item.quantity
            ReturnedSaleItem(
                store=store,
                sale_item=sale_item,
                returned_sale=returned_sale,
                quantity=quantity,
                batch=sale_item.batch,
            )
        return returned_sale

    #
    # Properties
    #

    @property
    def products(self):
        """All |saleitems| of this sale containing a |product|.

        :returns: the result set containing the |saleitems|, ordered
            by :attr:`stoqlib.domain.sellable.Sellable.code`
        """
        return self.store.find(
            SaleItem,
            And(SaleItem.sale_id == self.id,
                SaleItem.sellable_id == Product.sellable_id,
                SaleItem.sellable_id == Sellable.id)).order_by(
            Sellable.code)

    @property
    def services(self):
        """All |saleitems| of this sale containing a |service|.

        :returns: the result set containing the |saleitems|, ordered
            by :attr:`stoqlib.domain.sellable.Sellable.code`
        """
        return self.store.find(
            SaleItem,
            And(SaleItem.sale_id == self.id,
                SaleItem.sellable_id == Service.sellable_id,
                SaleItem.sellable_id == Sellable.id)).order_by(
            Sellable.code)

    @property
    def payments(self):
        """Returns all valid payments for this sale ordered by open date

        This will return a list of valid payments for this sale, that
        is, all payments on the |paymentgroups| that were not cancelled.
        If you need to get the cancelled too, use :obj:`.group.payments`.

        :returns: an ordered iterable of |payment|.
        """
        return self.group.get_valid_payments().order_by(Payment.open_date)

    def _get_discount_by_percentage(self):
        discount_value = self.discount_value
        if not discount_value:
            return Decimal(0)
        subtotal = self.get_sale_subtotal()
        assert subtotal > 0, ('the sale subtotal should not be zero '
                              'at this point')
        total = subtotal - discount_value
        percentage = (1 - total / subtotal) * 100
        return quantize(percentage)

    def _set_discount_by_percentage(self, value):
        self.discount_value = self._get_percentage_value(value)

    discount_percentage = property(_get_discount_by_percentage,
                                   _set_discount_by_percentage,
                                   doc=("""
        Sets a discount by percentage.

        Note that percentage must be added as an absolute value, in other
        words::

            sale.total_sale_amount = 200
            sale.discount_percentage = 5
            # the price of the sale will now be be `190`
        """
                                        ))

    def _get_surcharge_by_percentage(self):
        surcharge_value = self.surcharge_value
        if not surcharge_value:
            return Decimal(0)
        subtotal = self.get_sale_subtotal()
        assert subtotal > 0, ('the sale subtotal should not be zero '
                              'at this point')
        total = subtotal + surcharge_value
        percentage = ((total / subtotal) - 1) * 100
        return quantize(percentage)

    def _set_surcharge_by_percentage(self, value):
        self.surcharge_value = self._get_percentage_value(value)

    surcharge_percentage = property(_get_surcharge_by_percentage,
                                    _set_surcharge_by_percentage,
                                    doc=("""
        Sets a discount by percentage.

        Note that percentage must be added as an absolute value, in other
        words::

            sale.total_sale_amount = 200
            sale.surcharge_percentage = 5
            # the price of the sale will now be `210`

        """
                                         ))

    #
    #   NF-e api
    #

    def get_nfe_coupon_info(self):
        """Returns
        """
        if not self.coupon_id:
            return None

        # FIXME: we still dont have the number of the ecf stored in stoq
        # (note: this is not the serial number)
        return Settable(number=u'',
                        coo=self.coupon_id)

    #
    # Private API
    #

    def _set_sale_status(self, status):
        old_status = self.status
        self.status = status

        SaleStatusChangedEvent.emit(self, old_status)

    def _get_percentage_value(self, percentage):
        if not percentage:
            return currency(0)
        subtotal = self.get_sale_subtotal()
        percentage = Decimal(percentage)
        perc_value = subtotal * (percentage / Decimal(100))
        # discount/surchage cannot have more than 2 decimal points
        return quantize(currency(perc_value))


#
# Adapters
#


class SaleAdaptToPaymentTransaction(object):
    implements(IPaymentTransaction)

    def __init__(self, sale):
        self.sale = sale

    #
    # IPaymentTransaction
    #

    def confirm(self):
        self.sale.group.confirm()
        self._add_inpayments()
        self._create_fiscal_entries()

        if self._create_commission_at_confirm():
            for payment in self.sale.payments:
                self.create_commission(payment)

    def pay(self):
        # Right now commissions are created when the payment is confirmed
        # (if the parameter is set) or when the payment is confirmed.
        # This code is still here for the users that some payments created
        # (and paid) but no commission created yet.
        # This can be removed sometime in the future.
        for payment in self.sale.payments:
            self.create_commission(payment)

    def cancel(self):
        pass

    def return_(self, returned_sale):
        # TODO: As we are now supporting partial returns, all logic in here
        # were moved to stoqlib.domain.returned_sale. Is that the right
        # move, or can we expect some drawbacks? Thiago Bellini - 09/12/2012
        pass

    def create_commission(self, payment):
        """Creates a commission for the *payment*

        This will create a |commission| for the given |payment|,
        :obj:`.sale` and :obj:`.sale.salesperson`. Note that, if the
        payment already has a commission, nothing will be done.
        """
        from stoqlib.domain.commission import Commission
        if payment.has_commission():
            return

        commission = Commission(
            commission_type=self._get_commission_type(),
            sale=self.sale,
            payment=payment,
            salesperson=self.sale.salesperson,
            store=self.sale.store)
        if payment.is_outpayment():
            commission.value = -commission.value

        return commission

    #
    # Private
    #

    def _add_inpayments(self):
        payments = self.sale.payments
        if not payments.count():
            raise ValueError(
                _('You must have at least one payment for each payment group'))

        till = Till.get_current(self.sale.store)
        assert till
        for payment in payments:
            assert payment.is_inpayment()
            till.add_entry(payment)

    def _create_commission_at_confirm(self):
        store = self.sale.store
        return sysparam(store).SALE_PAY_COMMISSION_WHEN_CONFIRMED

    def _get_commission_type(self):
        from stoqlib.domain.commission import Commission

        nitems = 0
        for item in self.sale.payments:
            if not item.is_outpayment():
                nitems += 1

        if nitems <= 1:
            return Commission.DIRECT
        return Commission.INSTALLMENTS

    def _get_pm_commission_total(self):
        """Return the payment method commission total. Usually credit
        card payment method is the most common method which uses
        commission
        """
        return currency(0)

    def _get_icms_total(self, av_difference):
        """A Brazil-specific method
        Calculates the icms total value

        :param av_difference: the average difference for the sale items.
                              it means the average discount or surcharge
                              applied over all sale items
        """
        icms_total = Decimal(0)
        for item in self.sale.products:
            price = item.price + av_difference
            sellable = item.sellable
            tax_constant = sellable.get_tax_constant()
            if tax_constant is None or tax_constant.tax_type != TaxType.CUSTOM:
                continue
            icms_tax = tax_constant.tax_value / Decimal(100)
            icms_total += icms_tax * (price * item.quantity)

        return icms_total

    def _get_iss_total(self, av_difference):
        """A Brazil-specific method
        Calculates the iss total value

        :param av_difference: the average difference for the sale items.
                              it means the average discount or surcharge
                              applied over all sale items
        """
        iss_total = Decimal(0)
        store = self.sale.store
        iss_tax = sysparam(store).ISS_TAX / Decimal(100)
        for item in self.sale.services:
            price = item.price + av_difference
            iss_total += iss_tax * (price * item.quantity)
        return iss_total

    def _get_average_difference(self):
        sale = self.sale
        if sale.get_items().is_empty():
            raise DatabaseInconsistency(
                _(u"Sale orders must have items, which means products or "
                  u"services"))
        total_quantity = sale.get_items_total_quantity()
        if not total_quantity:
            raise DatabaseInconsistency(
                _(u"Sale total quantity should never be zero"))
        # If there is a discount or a surcharge applied in the whole total
        # sale amount, we must share it between all the item values
        # otherwise the icms and iss won't be calculated properly
        total = (sale.get_total_sale_amount() -
                 self._get_pm_commission_total())
        subtotal = sale.get_sale_subtotal()
        return (total - subtotal) / total_quantity

    def _get_iss_entry(self):
        return FiscalBookEntry.get_entry_by_payment_group(
            self.sale.store, self.sale.group,
            FiscalBookEntry.TYPE_SERVICE)

    def _create_fiscal_entries(self):
        """A Brazil-specific method
        Create new ICMS and ISS entries in the fiscal book
        for a given sale.

        Important: freight and interest are not part of the base value for
        ICMS. Only product values and surcharge which applies increasing the
        product totals are considered here.
        """
        sale = self.sale
        av_difference = self._get_average_difference()

        if not sale.products.is_empty():
            FiscalBookEntry.create_product_entry(
                sale.store,
                sale.group, sale.cfop, sale.coupon_id,
                self._get_icms_total(av_difference))

        if not sale.services.is_empty() and sale.service_invoice_number:
            FiscalBookEntry.create_service_entry(
                sale.store,
                sale.group, sale.cfop, sale.service_invoice_number,
                self._get_iss_total(av_difference))

Sale.registerFacet(SaleAdaptToPaymentTransaction, IPaymentTransaction)


#
# Views
#

class ReturnedSaleItemsView(Viewable):
    # returned and original sale item
    id = ReturnedSaleItem.id
    quantity = ReturnedSaleItem.quantity
    price = ReturnedSaleItem.price

    # returned and original sale
    _sale_id = Sale.id
    _new_sale_id = ReturnedSale.new_sale_id
    returned_identifier = ReturnedSale.identifier
    invoice_number = ReturnedSale.invoice_number
    return_date = ReturnedSale.return_date
    reason = ReturnedSale.reason

    # sellable
    sellable_id = ReturnedSaleItem.sellable_id
    code = Sellable.code
    description = Sellable.description

    # summaries
    total = SaleItem.price * ReturnedSaleItem.quantity

    tables = [
        ReturnedSaleItem,
        Join(SaleItem, SaleItem.id == ReturnedSaleItem.sale_item_id),
        Join(Sellable, Sellable.id == ReturnedSaleItem.sellable_id),
        Join(ReturnedSale, ReturnedSale.id == ReturnedSaleItem.returned_sale_id),
        Join(Sale, Sale.id == ReturnedSale.sale_id),
    ]

    @property
    def new_sale(self):
        if not self._new_sale_id:
            return None
        return Sale.get(self._new_sale_id, self.store)

    #
    #  Classmethods
    #

    @classmethod
    def find_by_sale(cls, store, sale):
        return store.find(cls, _sale_id=sale.id).order_by(ReturnedSale.return_date)


_SaleItemSummary = Select(columns=[SaleItem.sale_id,
                                   Alias(Sum(SaleItemIpi.v_ipi), 'v_ipi'),
                                   Alias(Sum(SaleItem.quantity), 'total_quantity'),
                                   Alias(Sum(SaleItem.quantity *
                                             SaleItem.price), 'subtotal')],
                          tables=[SaleItem,
                                  LeftJoin(SaleItemIpi,
                                           SaleItemIpi.id == SaleItem.ipi_info_id)],
                          group_by=[SaleItem.sale_id])
SaleItemSummary = Alias(_SaleItemSummary, '_sale_item')


class SaleView(Viewable):
    """Stores general informatios about sales

    :cvar id: the id of the sale table
    :cvar coupon_id: the id generated by the fiscal printer
    :cvar open_date: the date when the sale was started
    :cvar confirm_date: the date when the sale was confirmed
    :cvar close_date: the date when the sale was closed
    :cvar cancel_date: the date when the sale was cancelled
    :cvar notes: sale order general notes
    :cvar status: the sale status
    :cvar salesperson_name: the salesperson name
    :cvar client_name: the sale client name
    :cvar client_id: the if of the |client| table
    :cvar subtotal: the sum of all items in the sale
    :cvar surcharge_value: the sale surcharge value
    :cvar discount_value: the sale discount value
    :cvar total: the subtotal - discount + charge
    :cvar total_quantity: the items total quantity for the sale
    :cvar invoice_number: the sale invoice number
    """

    Person_Branch = ClassAlias(Person, 'person_branch')
    Person_Client = ClassAlias(Person, 'person_client')
    Person_SalesPerson = ClassAlias(Person, 'person_sales_person')

    sale = Sale
    client = Client

    # Sale
    id = Sale.id
    identifier = Sale.identifier
    identifier_str = Cast(Sale.identifier, 'text')
    invoice_number = Sale.invoice_number
    coupon_id = Sale.coupon_id
    open_date = Sale.open_date
    close_date = Sale.close_date
    confirm_date = Sale.confirm_date
    cancel_date = Sale.cancel_date
    return_date = Sale.return_date
    expire_date = Sale.expire_date
    status = Sale.status
    notes = Sale.notes
    surcharge_value = Sale.surcharge_value
    discount_value = Sale.discount_value
    branch_id = Sale.branch_id

    # Client Sales person Branch
    client_id = Client.id
    salesperson_name = Person_SalesPerson.name
    client_name = Person_Client.name
    branch_name = Person_Branch.name

    # Summaries
    v_ipi = Field('_sale_item', 'v_ipi')
    subtotal = Field('_sale_item', 'subtotal')
    total_quantity = Field('_sale_item', 'total_quantity')
    total = Field('_sale_item', 'subtotal') - \
        Sale.discount_value + Sale.surcharge_value

    tables = [
        Sale,
        Join(SaleItemSummary, Field('_sale_item', 'sale_id') == Sale.id),
        LeftJoin(Branch, Sale.branch_id == Branch.id),
        LeftJoin(Client, Sale.client_id == Client.id),
        LeftJoin(SalesPerson, Sale.salesperson_id == SalesPerson.id),

        LeftJoin(Person_Branch, Branch.person_id == Person_Branch.id),
        LeftJoin(Person_Client, Client.person_id == Person_Client.id),
        LeftJoin(Person_SalesPerson, SalesPerson.person_id == Person_SalesPerson.id),
    ]

    @classmethod
    def post_search_callback(cls, sresults):
        select = sresults.get_select_expr(Count(1), Sum(cls.total))
        return ('count', 'sum'), select

    #
    # Class methods
    #

    @classmethod
    def find_by_branch(cls, store, branch):
        if branch:
            return store.find(cls, Sale.branch == branch)

        return store.find(cls)

    #
    # Properties
    #

    @property
    def returned_sales(self):
        return self.store.find(ReturnedSale, sale_id=self.id)

    @property
    def return_total(self):
        store = self.store
        returned_items = store.find(ReturnedSaleItemsView, Sale.id == self.id)
        return currency(returned_items.sum(ReturnedSaleItemsView.total) or 0)

    #
    # Public API
    #

    def can_return(self):
        return (self.status == Sale.STATUS_CONFIRMED or
                self.status == Sale.STATUS_PAID)

    def can_confirm(self):
        return (self.status == Sale.STATUS_ORDERED or
                self.status == Sale.STATUS_QUOTE)

    def can_cancel(self):
        return self.status in (Sale.STATUS_CONFIRMED, Sale.STATUS_PAID,
                               Sale.STATUS_ORDERED, Sale.STATUS_QUOTE)

    def get_surcharge_value(self):
        return currency(self.surcharge_value or 0)

    def get_discount_value(self):
        return currency(self.discount_value or 0)

    def get_subtotal(self):
        if self.v_ipi is not None:
            return currency(self.subtotal + self.v_ipi)

        return currency(self.subtotal)

    def get_total(self):
        if self.v_ipi is not None:
            return currency(self.total + self.v_ipi)

        return currency(self.total)

    def get_client_name(self):
        return unicode(self.client_name or u"")

    def get_salesperson_name(self):
        return unicode(self.salesperson_name or u"")

    def get_open_date_as_string(self):
        return self.open_date.strftime("%x")

    def get_status_name(self):
        return Sale.get_status_name(self.status)


class ReturnedSaleView(Viewable):
    """Stores general informatios about returned sales."""

    # Alias for Branch Person Object
    Person_Branch = ClassAlias(Person, 'person_branch')
    # Alias for Client Person Object
    Person_Client = ClassAlias(Person, 'person_client')
    # Alias for Sales Person Sales Object
    Person_SalesPerson = ClassAlias(Person, 'person_sales_person')
    # Alias for Login User Person Object
    Person_LoginUser = ClassAlias(Person, 'person_login_user')

    # Current Sale
    sale = Sale
    # Current Client
    client = Client
    # Current Returned Sale
    returned_sale = ReturnedSale

    #: the id of the returned_sale table
    id = ReturnedSale.id

    #: a unique numeric identifer for the returned sale
    identifier = ReturnedSale.identifier
    identifier_str = Cast(ReturnedSale.identifier, 'text')
    invoice_number = ReturnedSale.invoice_number

    #: date of the return product
    return_date = ReturnedSale.return_date

    #: reason to return the sale
    reason = ReturnedSale.reason

    #: person_id of the responsible for return the sale
    responsible_id = ReturnedSale.responsible_id

    #: id of the sales branch
    branch_id = ReturnedSale.branch_id

    #: id of the new sale, if exist, an exchange of product or something else
    new_sale_id = ReturnedSale.new_sale_id

    #: Sale id
    sale_id = Sale.id

    #: value of the total of returned sale
    total = Sum(ReturnedSaleItem.price * ReturnedSaleItem.quantity)

    #: Client id
    client_id = Client.id
    #: Name of Sales Person Sales
    salesperson_name = Person_SalesPerson.name
    #: Name of Client Person
    client_name = Person_Client.name
    #: Name of Branch Person
    branch_name = Person_Branch.name
    # Name of Responsible for Returned Sale
    responsible_name = Person_LoginUser.name

    # Tables Queries
    tables = [
        ReturnedSale,
        Join(Sale, Sale.id == ReturnedSale.sale_id),
        LeftJoin(ReturnedSaleItem,
                 ReturnedSaleItem.returned_sale_id == ReturnedSale.id),
        LeftJoin(Sellable, Sellable.id == ReturnedSaleItem.sellable_id),
        LeftJoin(Branch, Sale.branch_id == Branch.id),
        LeftJoin(Client, Sale.client_id == Client.id),
        LeftJoin(SalesPerson, Sale.salesperson_id == SalesPerson.id),
        LeftJoin(LoginUser, LoginUser.id == ReturnedSale.responsible_id),
        LeftJoin(Person_Branch, Branch.person_id == Person_Branch.id),
        LeftJoin(Person_Client, Client.person_id == Person_Client.id),
        LeftJoin(Person_SalesPerson,
                 SalesPerson.person_id == Person_SalesPerson.id),
        LeftJoin(Person_LoginUser, Person_LoginUser.id == LoginUser.person_id)
    ]

    group_by = [id, sale_id, Sellable.id, client_id, branch_id, branch_name,
                salesperson_name, client_name, LoginUser.id, Person_LoginUser.name]
    #: Name of Sellable product
    product_name = Sellable.description


class SalePaymentMethodView(SaleView):

    # If a sale has more than one payment, it will appear as much times in the
    # search. Must always be used with select(distinct=True).
    tables = SaleView.tables[:]
    tables.append(LeftJoin(Payment, Sale.group_id == Payment.group_id))

    #
    # Class Methods
    #

    @classmethod
    def find_by_payment_method(cls, store, method):
        if method:
            results = store.find(cls, Payment.method == method)
        else:
            results = store.find(cls)

        results.config(distinct=True)
        return results


class SoldSellableView(Viewable):
    Person_Client = ClassAlias(Person, 'person_client')
    Person_SalesPerson = ClassAlias(Person, 'person_sales_person')

    id = Sellable.id
    code = Sellable.code
    description = Sellable.description

    client_id = Sale.client_id
    client_name = Person_Client.name

    # Aggregates
    total_quantity = Sum(SaleItem.quantity)
    subtotal = Sum(SaleItem.quantity * SaleItem.price)

    group_by = [id, code, description, client_id, client_name]

    tables = [
        Sellable,
        LeftJoin(SaleItem, SaleItem.sellable_id == Sellable.id),
        LeftJoin(Sale, Sale.id == SaleItem.sale_id),
        LeftJoin(Client, Sale.client_id == Client.id),
        LeftJoin(SalesPerson, Sale.salesperson_id == SalesPerson.id),
        LeftJoin(Person_Client, Client.person_id == Person_Client.id),
        LeftJoin(Person_SalesPerson, SalesPerson.person_id == Person_SalesPerson.id),
        LeftJoin(SaleItemIpi, SaleItemIpi.id == SaleItem.ipi_info_id),
    ]


class SoldServicesView(SoldSellableView):
    estimated_fix_date = SaleItem.estimated_fix_date

    group_by = SoldSellableView.group_by[:]
    group_by.append(estimated_fix_date)

    tables = SoldSellableView.tables[:]
    tables.append(Join(Service, Sellable.id == Service.sellable_id))


class SoldProductsView(SoldSellableView):
    # Aggregates
    last_date = Max(Sale.open_date)
    avg_value = Avg(SaleItem.price)
    quantity = Sum(SaleItem.quantity)
    total_value = Sum(SaleItem.quantity * SaleItem.price)

    tables = SoldSellableView.tables[:]
    tables.append(Join(Product, Sellable.id == Product.sellable_id))


class SalesPersonSalesView(Viewable):

    id = SalesPerson.id
    name = Person.name

    # aggregates
    total_amount = Sum(Sale.total_amount)
    total_quantity = Sum(Field('_sale_item', 'total_quantity'))
    total_sales = Count(Sale.id)

    group_by = [id, name]

    tables = [
        SalesPerson,
        LeftJoin(Sale, Sale.salesperson_id == SalesPerson.id),
        LeftJoin(SaleItemSummary, Field('_sale_item', 'sale_id') == Sale.id),
        LeftJoin(Person, Person.id == SalesPerson.person_id),
    ]

    clause = Or(Sale.status == Sale.STATUS_CONFIRMED,
                Sale.status == Sale.STATUS_PAID)

    @classmethod
    def find_by_date(cls, store, date):
        if date:
            if isinstance(date, tuple):
                date_query = And(Date(Sale.confirm_date) >= date[0],
                                 Date(Sale.confirm_date) <= date[1])
            else:
                date_query = Date(Sale.confirm_date) == date

            results = store.find(cls, date_query)
        else:
            results = store.find(cls)

        results.config(distinct=True)
        return results
