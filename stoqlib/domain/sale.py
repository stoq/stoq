# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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

import datetime
from decimal import Decimal

from kiwi.argcheck import argcheck
from kiwi.currency import currency
from kiwi.python import Settable
from stoqdrivers.enum import TaxType
from zope.interface import implements

from stoqlib.database.orm import AutoReload
from stoqlib.database.orm import (ForeignKey, UnicodeCol, DateTimeCol, IntCol,
                                  PriceCol, QuantityCol, MultipleJoin)
from stoqlib.database.orm import AND, const, Field, OR
from stoqlib.database.orm import Viewable, Alias, LeftJoin, Join
from stoqlib.database.runtime import (get_current_user,
                                      get_current_branch)
from stoqlib.domain.base import Domain
from stoqlib.domain.event import Event
from stoqlib.domain.events import (SaleStatusChangedEvent,
                                   DeliveryStatusChangedEvent)
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.interfaces import IContainer, IPaymentTransaction
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import (Person, Client, Branch,
                                   SalesPerson)
from stoqlib.domain.product import Product, ProductHistory
from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.service import Service
from stoqlib.domain.taxes import SaleItemIcms, SaleItemIpi
from stoqlib.domain.till import Till
from stoqlib.exceptions import (SellError, DatabaseInconsistency,
                                StoqlibError)
from stoqlib.lib.component import Adaptable
from stoqlib.lib.defaults import quantize
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext

#
# Base Domain Classes
#


class SaleItem(Domain):
    """An item of a |sellable| within a |sale|.

    Different from |sellable| which contains information about
    the base price, tax, etc, this contains the price in which
    *self* was sold, it's taxes, the quantity, etc.
    """

    #: the quantity of the of sold item in this sale
    quantity = QuantityCol()

    #: original value the |sellable| had when adding the sale item
    base_price = PriceCol()

    #: averiage cost of the items in this item
    average_cost = PriceCol(default=0)

    #: price of this item
    price = PriceCol()

    #: |sale| for this item
    sale = ForeignKey('Sale')

    #: |sellable| for this item
    sellable = ForeignKey('Sellable')

    #: |delivery| or None
    delivery = ForeignKey('Delivery', default=None)

    #: :class:`fiscal entry <stoqlib.domain.fiscal.CfopData>`
    cfop = ForeignKey('CfopData', default=None)

    #: user defined notes, currently only used by services
    notes = UnicodeCol(default=None)

    #: estimated date that *self* will be fixed, currently
    #: only used by services
    estimated_fix_date = DateTimeCol(default_factory=datetime.datetime.now)

    # FIXME: This doesn't appear to be used anywhere. Maybe we
    #        should remove it from the database
    completion_date = DateTimeCol(default=None)

    #: the :class:`stoqlib.domain.taxes.SaleItemIcms` tax for *self*
    icms_info = ForeignKey('SaleItemIcms')

    #: the :class:`stoqlib.domain.taxes.SaleItemIpi` tax for *self*
    ipi_info = ForeignKey('SaleItemIpi')

    @property
    def returned_quantity(self):
        return ReturnedSaleItem.selectBy(
            connection=self.get_connection(),
            sale_item=self).sum(ReturnedSaleItem.q.quantity) or Decimal('0')

    #
    #  Domain
    #

    def _create(self, id, **kw):
        if not 'kw' in kw:
            if not 'sellable' in kw:
                raise TypeError('You must provide a sellable argument')
            base_price = kw['sellable'].price
            kw['base_price'] = base_price
            if not kw.get('cfop'):
                kw['cfop'] = kw['sellable'].default_sale_cfop
            if not kw.get('cfop'):
                kw['cfop'] = sysparam(self._connection).DEFAULT_SALES_CFOP

            conn = kw.get('connection', self._connection)
            kw['ipi_info'] = SaleItemIpi(connection=conn)
            kw['icms_info'] = SaleItemIcms(connection=conn)
        Domain._create(self, id, **kw)

        if self.sellable.product:
            # Set ipi details before icms, since icms may depend on the ipi
            self.ipi_info.set_from_template(self.sellable.product.ipi_template)
            self.icms_info.set_from_template(self.sellable.product.icms_template)

    #
    #  Public API
    #

    def sell(self, branch):
        conn = self.get_connection()
        if not (branch and
                branch.id == get_current_branch(conn).id):
            raise SellError(_(u"Stoq still doesn't support sales for "
                              u"branch companies different than the "
                              u"current one"))

        if not self.sellable.can_be_sold():
            raise SellError(_(u"%r does not have enough stock to be sold.")
                              % self.sellable.get_description())

        storable = self.sellable.product_storable
        if storable:
            item = storable.decrease_stock(self.quantity, branch)
            self.average_cost = item.stock_cost

    def cancel(self, branch):
        storable = self.sellable.product_storable
        if storable:
            storable.increase_stock(self.quantity - self.returned_quantity,
                                    branch)

    def get_total(self):
        # Sale items are suposed to have only 2 digits, but the value price
        # * quantity may have more than 2, so we need to round it.
        if self.ipi_info:
            return currency(quantize(self.price * self.quantity +
                                     self.ipi_info.v_ipi))
        return currency(quantize(self.price * self.quantity))

    def get_quantity_unit_string(self):
        return "%s %s" % (self.quantity, self.sellable.get_unit_description())

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
        service = Service.selectOneBy(sellable=self.sellable,
                                      connection=self.get_connection())
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
                return '5929'
            else:
                return '6929'

        if self.cfop:
            return self.cfop.code.replace('.', '')

        # FIXME: remove sale cfop?
        return self.sale.cfop.code.replace('.', '')


class Delivery(Domain):
    """Delivery, transporting a set of sale items for sale.

    Involves a |transporter| transporting a set of |saleitems| to a
    receival |address|.

    Optionally a :obj:`.tracking_code` can be set to track the items.
    """

    implements(IContainer)

    #: The delivery was created
    STATUS_INITIAL = 0

    #: sent to deliver
    STATUS_SENT = 1

    #: received by the |client|
    STATUS_RECEIVED = 2

    statuses = {STATUS_INITIAL: _("Waiting"),
                STATUS_SENT: _("Sent"),
                STATUS_RECEIVED: _("Received")}

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
    tracking_code = UnicodeCol(default='')

    #: the |address| to deliver to
    address = ForeignKey('Address', default=None)

    #: the |transporter| for this delivery
    transporter = ForeignKey('Transporter', default=None)

    #: the |saleitem| for the delivery itself
    service_item = ForeignKey('SaleItem', default=None)

    #: the |saleitems| for the items to deliver
    delivery_items = MultipleJoin('SaleItem', joinColumn='delivery_id')

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
        return ''

    @property
    def client_str(self):
        client = self.service_item.sale.client
        if client:
            return client.get_description()
        return ''

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
    #  ORMObject hooks
    #

    def _create(self, id, **kwargs):
        if not 'open_date' in kwargs:
            kwargs['open_date'] = const.NOW()

        super(Delivery, self)._create(id, **kwargs)

    #
    #  IContainer implementation
    #

    @argcheck(SaleItem)
    def add_item(self, item):
        item.delivery = self

    def get_items(self):
        return list(self.delivery_items)

    @argcheck(SaleItem)
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

    """

    implements(IContainer)

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
    #: :obj:`.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IntCol(default=AutoReload)

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
    notes = UnicodeCol(default='')

    #: the date sale was created, this is always set
    open_date = DateTimeCol(default_factory=datetime.datetime.now)

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
    operation_nature = UnicodeCol(default='')

    #: the :class:`fiscal entry <stoqlib.domain.fiscal.CfopData>`
    cfop = ForeignKey("CfopData")

    #: the |client| who this sale was sold to
    client = ForeignKey('Client', default=None)

    #: the |salesperson| who sold the sale
    salesperson = ForeignKey('SalesPerson')

    #: the |branch| this sale belongs to
    branch = ForeignKey('Branch')

    # FIXME: transporter should only be used on Delivery.
    #: If we have a delivery, this is the |transporter| for this sale
    transporter = ForeignKey('Transporter', default=None)

    #: the |paymentgroup| of this sale
    group = ForeignKey('PaymentGroup')

    #: the |clientcategory| used for price determination.
    client_category = ForeignKey('ClientCategory', default=None)

    def _init(self, *args, **kwargs):
        self.addFacet(IPaymentTransaction)
        Domain._init(self, *args, **kwargs)
    #
    # ORMObject hooks
    #

    def _create(self, id, **kw):
        conn = self.get_connection()
        if not 'cfop' in kw:
            kw['cfop'] = sysparam(conn).DEFAULT_SALES_CFOP
        Domain._create(self, id, **kw)

    #
    # Classmethods
    #

    @classmethod
    def get_status_name(cls, status):
        """The :obj:`.status` as a translated string"""
        if not status in cls.statuses:
            raise DatabaseInconsistency(_("Invalid status %d") % status)
        return cls.statuses[status]

    @classmethod
    def get_last_confirmed(cls, conn):
        """Fetch the last confirmed sale
        :param conn: a database connection
        """
        results = cls.select(AND(cls.q.status == cls.STATUS_CONFIRMED,
                                 cls.q.confirm_date != None),
                             orderBy='-confirm_date',
                             connection=conn).limit(1)
        if results:
            return results[0]

    @classmethod
    def get_last_invoice_number(cls, conn):
        """Returns the last sale invoice number. If there is not an invoice
        number used, the returned value will be zero.

        :param conn: a database connection
        :returns: an integer representing the last sale invoice number
        """
        return cls.select(connection=conn).max('invoice_number') or 0

    #
    # IContainer implementation
    #

    @argcheck(SaleItem)
    def add_item(self, sale_item):
        assert not sale_item.sale
        sale_item.sale = self

    def get_items(self):
        conn = self.get_connection()
        return SaleItem.selectBy(sale=self,
                                 connection=conn).orderBy(SaleItem.q.id)

    @argcheck(SaleItem)
    def remove_item(self, sale_item):
        SaleItem.delete(sale_item.id, connection=self.get_connection())

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
        """Only confirmed sales can be paid

        :returns: ``True`` if the sale can be set as paid
        """
        return self.status == Sale.STATUS_CONFIRMED

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
        return self.payments.filterBy(
            status=Payment.STATUS_PENDING).count() > 0

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
        if not self.get_items():
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
        """
        assert self.can_confirm()
        assert self.branch

        # FIXME: We should use self.branch, but it's not supported yet
        conn = self.get_connection()
        branch = get_current_branch(conn)
        for item in self.get_items():
            if item.sellable.product:
                ProductHistory.add_sold_item(conn, branch, item)
            item.sell(branch)

        self.total_amount = self.get_total_sale_amount()

        transaction = IPaymentTransaction(self)
        transaction.confirm()

        if self.client:
            self.group.payer = self.client.person

        self.confirm_date = const.NOW()
        self._set_sale_status(Sale.STATUS_CONFIRMED)

        # do not log money payments twice
        if not self.only_paid_with_money():
            if self.client:
                msg = _("Sale {sale_number} to client {client_name} was "
                        "confirmed with value {total_value:.2f}.").format(
                        sale_number=self.get_order_number_str(),
                        client_name=self.client.person.name,
                        total_value=self.get_total_sale_amount())
            else:
                msg = _("Sale {sale_number} without a client was "
                        "confirmed with value {total_value:.2f}.").format(
                        sale_number=self.get_order_number_str(),
                        total_value=self.get_total_sale_amount())
            Event.log(Event.TYPE_SALE, msg)

    def set_paid(self):
        """Mark the sale as paid
        Marking a sale as paid means that all the payments have been received.
        """
        assert self.can_set_paid()

        for payment in self.payments:
            if not payment.is_paid():
                raise StoqlibError(
                    _("You cannot close a sale without paying all the payment. "
                      "Payment %r is still not paid") % (payment, ))

        transaction = IPaymentTransaction(self)
        transaction.pay()

        self.close_date = const.NOW()
        self._set_sale_status(Sale.STATUS_PAID)

        if self.only_paid_with_money():
            # Money payments are confirmed and paid, so lof them that way
            if self.client:
                msg = _("Sale {sale_number} to client {client_name} was paid "
                        "and confirmed with value {total_value:.2f}.").format(
                        sale_number=self.get_order_number_str(),
                        client_name=self.client.person.name,
                        total_value=self.get_total_sale_amount())
            else:
                msg = _("Sale {sale_number} without a client was paid "
                        "and confirmed with value {total_value:.2f}.").format(
                        sale_number=self.get_order_number_str(),
                        total_value=self.get_total_sale_amount())
        else:
            if self.client:
                msg = _("Sale {sale_number} to client {client_name} was paid "
                        "with value {total_value:.2f}.").format(
                        sale_number=self.get_order_number_str(),
                        client_name=self.client.person.name,
                        total_value=self.get_total_sale_amount())
            else:
                msg = _("Sale {sale_number} without a client was paid "
                        "with value {total_value:.2f}.").format(
                        sale_number=self.get_order_number_str(),
                        total_value=self.get_total_sale_amount())
        Event.log(Event.TYPE_SALE, msg)

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

        self.close_date = const.NOW()
        self._set_sale_status(Sale.STATUS_RENEGOTIATED)

    def cancel(self):
        """Cancel the sale
        You can only cancel an ordered sale.
        This does not cancel the payments, only the sale items.
        """
        assert self.can_cancel()

        # ordered and quote sale items did not change the stock of such items
        if (self.status != Sale.STATUS_ORDERED and
            self.status != Sale.STATUS_QUOTE):
            branch = get_current_branch(self.get_connection())
            for item in self.get_items():
                item.cancel(branch)

        self.cancel_date = const.NOW()
        self._set_sale_status(Sale.STATUS_CANCELLED)

    def return_(self, returned_sale):
        """Returns a sale
        Returning a sale means that all the items are returned to the item.
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
            self.return_date = const.NOW()
            self._set_sale_status(Sale.STATUS_RETURNED)

        transaction = IPaymentTransaction(self)
        transaction.return_(returned_sale)

        if self.client:
            if totally_returned:
                msg = _("Sale {sale_number} to client {client_name} was "
                        "totally returned with value {total_value:.2f}. "
                        "Reason: {reason}")
            else:
                msg = _("Sale {sale_number} to client {client_name} was "
                        "partially returned with value {total_value:.2f}. "
                        "Reason: {reason}")
            msg = msg.format(sale_number=self.get_order_number_str(),
                             client_name=self.client.person.name,
                             total_value=returned_sale.returned_total,
                             reason=returned_sale.reason)
        else:
            if totally_returned:
                msg = _("Sale {sale_number} without a client was "
                        "totally returned with value {total_value:.2f}. "
                        "Reason: {reason}")
            else:
                msg = _("Sale {sale_number} without a client was "
                        "partially returned with value {total_value:.2f}. "
                        "Reason: {reason}")
            msg = msg.format(sale_number=self.get_order_number_str(),
                             total_value=returned_sale.returned_total,
                             reason=returned_sale.reason)

        Event.log(Event.TYPE_SALE, msg)

    #
    # Accessors
    #

    def get_total_sale_amount(self):
        """
        Fetches the total value  paid by the |client|.
        It can be calculated as::

            Sale total = Sum(product and service prices) + surcharge +
                             interest - discount

        :returns: the total value
        """
        surcharge_value = self.surcharge_value or Decimal(0)
        discount_value = self.discount_value or Decimal(0)
        subtotal = self.get_sale_subtotal()
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
        return self.get_items().sum('quantity') or Decimal(0)

    def get_total_paid(self):
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
                details.append(_('Delivery Address: %s') %
                               delivery.address.get_address_string())
                # At the moment, we just support only one delivery per sale.
                delivery_added = True
                delivery = None
            else:
                if sale_item.notes:
                    details.append(_('"%s" Notes: %s') % (
                        sale_item.get_description(), sale_item.notes))
            if sale_item.is_service() and sale_item.estimated_fix_date:
                details.append(_('"%s" Estimated Fix Date: %s') % (
                                 sale_item.get_description(),
                                 sale_item.estimated_fix_date.strftime('%x')))
        return u'\n'.join(details)

    def get_order_number_str(self):
        # FIXME: Add branch acronym name in front
        return u'%05d' % self.identifier

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
                _("The sale %r have a client but no "
                  "client_role defined.") % self)

        return client_role

    # Other methods

    def only_paid_with_money(self):
        """Find out if the sale is paid using money

        :returns: ``True`` if the sale was paid with money
        """
        if not self.payments:
            return False
        return all(payment.is_money() for payment in self.payments)

    def add_sellable(self, sellable, quantity=1, price=None):
        """Adds a new item to a sale.

        :param sellable: the |sellable|
        :param quantity: quantity to add, defaults to 1
        :param price: optional, the price, it not set the price
          from the sellable will be used
        :returns: a |saleitem| for representing the
          sellable within this sale.
        """
        price = price or sellable.price
        return SaleItem(connection=self.get_connection(),
                        quantity=quantity,
                        sale=self,
                        sellable=sellable,
                        price=price)

    def create_sale_return_adapter(self):
        conn = self.get_connection()
        current_user = get_current_user(conn)
        returned_sale = ReturnedSale(
            connection=conn,
            sale=self,
            branch=get_current_branch(conn),
            responsible=current_user,
            )
        for sale_item in self.get_items():
            if sale_item.is_totally_returned():
                # Exclude quantities already returned from this one
                continue
            quantity = sale_item.quantity - sale_item.returned_quantity
            ReturnedSaleItem(
                connection=conn,
                sale_item=sale_item,
                returned_sale=returned_sale,
                quantity=quantity,
                )
        return returned_sale

    #
    # Properties
    #

    @property
    def order_number(self):
        return self.identifier

    @property
    def products(self):
        """All |saleitems| of this sale containing a |product|.
        """
        return SaleItem.select(
            AND(SaleItem.q.sale_id == self.id,
                SaleItem.q.sellable_id == Product.q.sellable_id),
            connection=self.get_connection()).orderBy('id')

    @property
    def services(self):
        """All |saleitems| of this sale containing a |service|.
        """
        return SaleItem.select(
            AND(SaleItem.q.sale_id == self.id,
                SaleItem.q.sellable_id == Service.q.sellable_id),
            connection=self.get_connection()).orderBy('id')

    @property
    def payments(self):
        """Returns all valid payments for this sale ordered by open date

        This will return a list of valid payments for this sale, that
        is, all payments on the |paymentgroups| that were not cancelled.
        If you need to get the cancelled too, use :obj:`.group.payments`.

        :returns: an ordered iterable of |payment|.
        """
        return self.group.get_valid_payments().orderBy(Payment.q.open_date)

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
                                   doc=(
        """Sets a discount by percentage.
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
                                    doc=(
        """Sets a discount by percentage.
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
        return Settable(number='',
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
        return currency(perc_value)


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
                self._create_commission(payment)

    def pay(self):
        if self._create_commission_at_confirm():
            return
        for payment in self.sale.payments:
            # FIXME: This shouldn't be needed, something is called
            #        twice where it shouldn't be
            if self._already_have_commission(payment):
                continue
            commission = self._create_commission(payment)
            if payment.is_outpayment():
                commission.value = -commission.value

    def cancel(self):
        pass

    def return_(self, returned_sale):
        # TODO: As we are now supporting partial returns, all logic in here
        # were moved to stoqlib.domain.returned_sale. Is that the right
        # move, or can we expect some drawbacks? Thiago Bellini - 09/12/2012
        pass

    #
    # Private API
    #

    def _create_commission(self, payment):
        from stoqlib.domain.commission import Commission
        return Commission(commission_type=self._get_commission_type(),
                          sale=self.sale,
                          payment=payment,
                          salesperson=self.sale.salesperson,
                          connection=self.sale.get_connection())

    def _add_inpayments(self):
        payments = self.sale.payments
        if not payments.count():
            raise ValueError(
                _('You must have at least one payment for each payment group'))

        till = Till.get_current(self.sale.get_connection())
        assert till
        for payment in payments:
            assert payment.is_inpayment()
            till.add_entry(payment)

        # FIXME: Move this to a payment method specific hook
        if payments.count() == 1 and payment.is_money():
            self.sale.group.pay()
            self.pay()

    def _create_commission_at_confirm(self):
        conn = self.sale.get_connection()
        return sysparam(conn).SALE_PAY_COMMISSION_WHEN_CONFIRMED

    def _get_commission_type(self):
        from stoqlib.domain.commission import Commission

        nitems = 0
        for item in self.sale.payments:
            if not item.is_outpayment():
                nitems += 1

        if nitems <= 1:
            return Commission.DIRECT
        return Commission.INSTALLMENTS

    def _already_have_commission(self, payment):
        from stoqlib.domain.commission import Commission

        commission = Commission.selectOneBy(
            payment=payment,
            connection=self.sale.get_connection())
        return commission is not None

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
        conn = self.sale.get_connection()
        iss_tax = sysparam(conn).ISS_TAX / Decimal(100)
        for item in self.sale.services:
            price = item.price + av_difference
            iss_total += iss_tax * (price * item.quantity)
        return iss_total

    def _get_average_difference(self):
        sale = self.sale
        if not sale.get_items().count():
            raise DatabaseInconsistency(
                _("Sale orders must have items, which means products or "
                  "services"))
        total_quantity = sale.get_items_total_quantity()
        if not total_quantity:
            raise DatabaseInconsistency(
                _("Sale total quantity should never be zero"))
        # If there is a discount or a surcharge applied in the whole total
        # sale amount, we must share it between all the item values
        # otherwise the icms and iss won't be calculated properly
        total = (sale.get_total_sale_amount() -
                 self._get_pm_commission_total())
        subtotal = sale.get_sale_subtotal()
        return (total - subtotal) / total_quantity

    def _get_iss_entry(self):
        return FiscalBookEntry.get_entry_by_payment_group(
            self.sale.get_connection(), self.sale.group,
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

        if sale.products:
            FiscalBookEntry.create_product_entry(
                sale.get_connection(),
                sale.group, sale.cfop, sale.coupon_id,
                self._get_icms_total(av_difference))

        if sale.services and sale.service_invoice_number:
            FiscalBookEntry.create_service_entry(
                sale.get_connection(),
                sale.group, sale.cfop, sale.service_invoice_number,
                self._get_iss_total(av_difference))

Sale.registerFacet(SaleAdaptToPaymentTransaction, IPaymentTransaction)


#
# Views
#

class _SaleItemSummary(Viewable):
    columns = dict(
        id=SaleItem.q.sale_id,
        v_ipi=const.SUM(SaleItemIpi.q.v_ipi),
        total_quantity=const.SUM(SaleItem.q.quantity),
        subtotal=const.SUM(SaleItem.q.quantity * SaleItem.q.price),
    )

    joins = [
        LeftJoin(SaleItemIpi,
                   SaleItemIpi.q.id == SaleItem.q.ipi_info_id),
    ]


class ReturnedSaleItemsView(Viewable):
    columns = dict(
        # returned and original sale item
        id=ReturnedSaleItem.q.id,
        quantity=ReturnedSaleItem.q.quantity,
        price=ReturnedSaleItem.q.price,

        # returned and original sale
        _sale_id=Sale.q.id,
        _new_sale_id=ReturnedSale.q.new_sale_id,
        invoice_number=ReturnedSale.q.invoice_number,
        return_date=ReturnedSale.q.return_date,
        reason=ReturnedSale.q.reason,

        # sellable
        code=Sellable.q.code,
        description=Sellable.q.description,

        # summaries
        total=SaleItem.q.price * ReturnedSaleItem.q.quantity,
        )

    joins = [
        Join(SaleItem,
                    SaleItem.q.id == ReturnedSaleItem.q.sale_item_id),
        Join(Sellable,
                    Sellable.q.id == ReturnedSaleItem.q.sellable_id),
        Join(ReturnedSale,
                    ReturnedSale.q.id == ReturnedSaleItem.q.returned_sale_id),
        Join(Sale,
                    Sale.q.id == ReturnedSale.q.sale_id),
        ]

    @property
    def new_sale(self):
        if not self._new_sale_id:
            return None
        return Sale.get(self._new_sale_id, self.get_connection())

    #
    #  Classmethods
    #

    @classmethod
    def select_by_sale(cls, sale, conn):
        return cls.select(Sale.q.id == sale.id,
                          connection=conn).orderBy(ReturnedSale.q.return_date)


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

    Person_Branch = Alias(Person, 'person_branch')
    Person_Client = Alias(Person, 'person_client')
    Person_SalesPerson = Alias(Person, 'person_sales_person')
    SaleItemSummary = Alias(_SaleItemSummary, '_sale_item')

    columns = dict(
        # Sale
        id=Sale.q.id,
        identifier=Sale.q.identifier,
        invoice_number=Sale.q.invoice_number,
        coupon_id=Sale.q.coupon_id,
        open_date=Sale.q.open_date,
        close_date=Sale.q.close_date,
        confirm_date=Sale.q.confirm_date,
        cancel_date=Sale.q.cancel_date,
        return_date=Sale.q.return_date,
        expire_date=Sale.q.expire_date,
        status=Sale.q.status,
        notes=Sale.q.notes,
        surcharge_value=Sale.q.surcharge_value,
        discount_value=Sale.q.discount_value,
        branch_id=Sale.q.branch_id,

        # Client, Sales person, Branch
        client_id=Client.q.id,
        salesperson_name=Person_SalesPerson.q.name,
        client_name=Person_Client.q.name,
        branch_name=Person_Branch.q.name,

        # Summaries
        v_ipi=Field('_sale_item', 'v_ipi'),
        subtotal=Field('_sale_item', 'subtotal'),
        total_quantity=Field('_sale_item', 'total_quantity'),
        total=Field('_sale_item', 'subtotal') - \
              Sale.q.discount_value + Sale.q.surcharge_value
    )

    joins = [
        Join(SaleItemSummary,
             Field('_sale_item', 'id') == Sale.q.id),
        LeftJoin(Branch,
                 Sale.q.branch_id == Branch.q.id),
        LeftJoin(Client,
                 Sale.q.client_id == Client.q.id),
        LeftJoin(SalesPerson,
                 Sale.q.salesperson_id == SalesPerson.q.id),

        LeftJoin(Person_Branch,
                 Branch.q.person_id == Person_Branch.q.id),
        LeftJoin(Person_Client,
                 Client.q.person_id == Person_Client.q.id),
        LeftJoin(Person_SalesPerson,
                 SalesPerson.q.person_id == Person_SalesPerson.q.id),
    ]

    @classmethod
    def post_search_callback(cls, sresults):
        select = sresults.get_select_expr(const.COUNT(1), const.SUM(cls.total))
        return ('count', 'sum'), select

    #
    # Class methods
    #

    @classmethod
    def select_by_branch(cls, query, branch, having=None, connection=None):
        if branch:
            branch_query = (Sale.q.branch == branch)
            if query:
                query = AND(query, branch_query)
            else:
                query = branch_query

        return cls.select(query, having=having, connection=connection)

    #
    # Properties
    #

    @property
    def sale(self):
        return Sale.get(self.id, self.get_connection())

    @property
    def returned_sales(self):
        return ReturnedSale.select(ReturnedSale.q.sale_id == self.id,
                                   connection=self.get_connection())

    @property
    def return_total(self):
        conn = self.get_connection()
        returned_items = ReturnedSaleItemsView.select(Sale.q.id == self.id,
                                                      connection=conn)
        return currency(returned_items.sum(ReturnedSaleItemsView.q.total) or 0)

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
        return unicode(self.client_name or "")

    def get_salesperson_name(self):
        return unicode(self.salesperson_name or "")

    def get_order_number_str(self):
        return u"%05d" % self.identifier

    def get_open_date_as_string(self):
        return self.open_date.strftime("%x")

    def get_status_name(self):
        return Sale.get_status_name(self.status)


class SalePaymentMethodView(SaleView):
    # If a sale has more than one payment, it will appear as much times in the
    # search. Must always be used with select(distinct=True).
    joins = SaleView.joins[:]
    joins.append(LeftJoin(Payment,
                 Sale.q.group_id == Payment.q.group_id))

    #
    # Class Methods
    #

    @classmethod
    def select_by_payment_method(cls, method, query=None, having=None,
                                 connection=None):
        if method:
            method_query = (Payment.q.method == method)
            if query:
                query = AND(query, method_query)
            else:
                query = method_query

        return cls.select(query, having=having, connection=connection,
                          distinct=True)


class SoldSellableView(Viewable):
    Person_Client = Alias(Person, 'person_client')
    Person_SalesPerson = Alias(Person, 'person_sales_person')

    columns = dict(
        id=Sellable.q.id,
        code=Sellable.q.code,
        description=Sellable.q.description,

        client_id=Sale.q.client_id,
        client_name=Person_Client.q.name,
        total_quantity=const.SUM(SaleItem.q.quantity),
        subtotal=const.SUM(SaleItem.q.quantity * SaleItem.q.price),
    )

    joins = [
        LeftJoin(SaleItem,
                    SaleItem.q.sellable_id == Sellable.q.id),
        LeftJoin(Sale,
                    Sale.q.id == SaleItem.q.sale_id),
        LeftJoin(Client,
                   Sale.q.client_id == Client.q.id),
        LeftJoin(SalesPerson,
                   Sale.q.salesperson_id == SalesPerson.q.id),

        LeftJoin(Person_Client,
                   Client.q.person_id == Person_Client.q.id),
        LeftJoin(Person_SalesPerson,
                   SalesPerson.q.person_id == Person_SalesPerson.q.id),

        LeftJoin(SaleItemIpi,
                   SaleItemIpi.q.id == SaleItem.q.ipi_info_id),
    ]


class SoldServicesView(SoldSellableView):
    columns = SoldSellableView.columns.copy()
    columns.update(dict(
        id=SaleItem.q.id,
        estimated_fix_date=SaleItem.q.estimated_fix_date,
    ))

    joins = SoldSellableView.joins[:]
    joins[0] = LeftJoin(Sellable,
                    SaleItem.q.sellable_id == Sellable.q.id)
    joins.append(
        Join(Service,
                    Sellable.q.id == Service.q.sellable_id),
    )


class SoldProductsView(SoldSellableView):
    columns = SoldSellableView.columns.copy()

    columns.update(dict(
        last_date=const.MAX(Sale.q.open_date),
        avg_value=const.AVG(SaleItem.q.price),
        quantity=const.SUM(SaleItem.q.quantity),
        total_value=const.SUM(SaleItem.q.quantity * SaleItem.q.price),
    ))

    joins = SoldSellableView.joins[:]
    joins.append(
        Join(Product,
                    Sellable.q.id == Product.q.sellable_id),
    )


class SalesPersonSalesView(Viewable):
    SaleItemSummary = Alias(_SaleItemSummary, '_sale_item')

    columns = dict(
        id=SalesPerson.q.id,
        name=Person.q.name,
        total_amount=const.SUM(Sale.q.total_amount),
        total_quantity=const.SUM(Field('_sale_item', 'total_quantity')),
        total_sales=const.COUNT(Sale.q.id)
    )

    joins = [
        LeftJoin(Sale,
                   Sale.q.salesperson_id == SalesPerson.q.id),
        LeftJoin(SaleItemSummary,
                   Field('_sale_item', 'id') == Sale.q.id),
        LeftJoin(Person,
                   Person.q.id == SalesPerson.q.person_id),
    ]

    clause = OR(Sale.q.status == Sale.STATUS_CONFIRMED,
                Sale.q.status == Sale.STATUS_PAID)

    @classmethod
    def select_by_date(cls, date, query=None, having=None,
                       connection=None):
        if date:
            if isinstance(date, tuple):
                date_query = AND(const.DATE(Sale.q.confirm_date) >= date[0],
                                 const.DATE(Sale.q.confirm_date) <= date[1])
            else:
                date_query = const.DATE(Sale.q.confirm_date) == date

            if query:
                query = AND(query, date_query)
            else:
                query = date_query

        return cls.select(query, having=having, connection=connection,
                          distinct=True)
