# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Receiving management """

# pylint: enable=E1101

from decimal import Decimal
import collections

from kiwi.currency import currency
from storm.expr import And, Eq
from storm.references import Reference, ReferenceSet

from stoqlib.database.properties import (PriceCol, QuantityCol, IntCol,
                                         DateTimeCol, UnicodeCol, IdentifierCol,
                                         IdCol, EnumCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.product import (ProductHistory, StockTransactionHistory,
                                    StorableBatch)
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.defaults import quantize
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ReceivingOrderItem(Domain):
    """This class stores information of the purchased items.

    Note that objects of this type should not be created manually, only by
    calling Receiving
    """

    __storm_table__ = 'receiving_order_item'

    #: the total quantity received for a certain |product|
    quantity = QuantityCol()

    #: the cost for each |product| received
    cost = PriceCol()

    purchase_item_id = IdCol()

    purchase_item = Reference(purchase_item_id, 'PurchaseItem.id')

    # FIXME: This could be a product instead of a sellable, since we only buy
    # products from the suppliers.
    sellable_id = IdCol()

    #: the |sellable|
    sellable = Reference(sellable_id, 'Sellable.id')

    batch_id = IdCol()

    #: If the sellable is a storable, the |batch| that it was received in
    batch = Reference(batch_id, 'StorableBatch.id')

    receiving_order_id = IdCol()

    receiving_order = Reference(receiving_order_id, 'ReceivingOrder.id')

    parent_item_id = IdCol()
    parent_item = Reference(parent_item_id, 'ReceivingOrderItem.id')

    children_items = ReferenceSet('id', 'ReceivingOrderItem.parent_item_id')

    #
    # Properties
    #

    @property
    def unit_description(self):
        unit = self.sellable.unit
        return u"%s" % (unit and unit.description or u"")

    #
    # Accessors
    #

    def get_remaining_quantity(self):
        """Get the remaining quantity from the purchase order this item
        is included in.
        :returns: the remaining quantity
        """
        return self.purchase_item.get_pending_quantity()

    def get_total(self):
        # We need to use the the purchase_item cost, since the current cost
        # might be different.
        cost = self.purchase_item.cost
        return currency(self.quantity * cost)

    def get_quantity_unit_string(self):
        unit = self.sellable.unit
        data = u"%s %s" % (self.quantity,
                           unit and unit.description or u"")
        # The unit may be empty
        return data.strip()

    def add_stock_items(self):
        """This is normally called from ReceivingOrder when
        a the receving order is confirmed.
        """
        store = self.store
        if self.quantity > self.get_remaining_quantity():
            raise ValueError(
                u"Quantity received (%d) is greater than "
                u"quantity ordered (%d)" % (self.quantity,
                                            self.get_remaining_quantity()))

        branch = self.receiving_order.branch
        storable = self.sellable.product_storable
        purchase = self.purchase_item.order
        if storable is not None:
            storable.increase_stock(self.quantity, branch,
                                    StockTransactionHistory.TYPE_RECEIVED_PURCHASE,
                                    self.id, self.cost, batch=self.batch)
        purchase.increase_quantity_received(self.purchase_item, self.quantity)
        ProductHistory.add_received_item(store, branch, self)


class ReceivingOrder(Domain):
    """Receiving order definition.
    """

    __storm_table__ = 'receiving_order'

    #: Products in the order was not received or received partially.
    STATUS_PENDING = u'pending'

    #: All products in the order has been received then the order is closed.
    STATUS_CLOSED = u'closed'

    FREIGHT_FOB_PAYMENT = u'fob-payment'
    FREIGHT_FOB_INSTALLMENTS = u'fob-installments'
    FREIGHT_CIF_UNKNOWN = u'cif-unknown'
    FREIGHT_CIF_INVOICE = u'cif-invoice'

    freight_types = collections.OrderedDict([
        (FREIGHT_FOB_PAYMENT, _(u"FOB - Freight value on a new payment")),
        (FREIGHT_FOB_INSTALLMENTS, _(u"FOB - Freight value on installments")),
        (FREIGHT_CIF_UNKNOWN, _(u"CIF - Freight value is unknown")),
        (FREIGHT_CIF_INVOICE, _(u"CIF - Freight value highlighted on invoice")),
    ])

    FOB_FREIGHTS = (FREIGHT_FOB_PAYMENT,
                    FREIGHT_FOB_INSTALLMENTS, )
    CIF_FREIGHTS = (FREIGHT_CIF_UNKNOWN,
                    FREIGHT_CIF_INVOICE)

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: status of the order
    status = EnumCol(allow_none=False, default=STATUS_PENDING)

    #: Date that order has been closed.
    receival_date = DateTimeCol(default_factory=localnow)

    #: Date that order was send to Stock application.
    confirm_date = DateTimeCol(default=None)

    #: Some optional additional information related to this order.
    notes = UnicodeCol(default=u'')

    #: Type of freight
    freight_type = EnumCol(allow_none=False, default=FREIGHT_FOB_PAYMENT)

    #: Total of freight paid in receiving order.
    freight_total = PriceCol(default=0)

    surcharge_value = PriceCol(default=0)

    #: Discount value in receiving order's payment.
    discount_value = PriceCol(default=0)

    #: Secure value paid in receiving order's payment.
    secure_value = PriceCol(default=0)

    #: Other expenditures paid in receiving order's payment.
    expense_value = PriceCol(default=0)

    # This is Brazil-specific information
    icms_total = PriceCol(default=0)
    ipi_total = PriceCol(default=0)

    #: The number of the order that has been received.
    invoice_number = IntCol()
    invoice_total = PriceCol(default=None)

    cfop_id = IdCol()
    cfop = Reference(cfop_id, 'CfopData.id')

    responsible_id = IdCol()
    responsible = Reference(responsible_id, 'LoginUser.id')

    supplier_id = IdCol()
    supplier = Reference(supplier_id, 'Supplier.id')

    branch_id = IdCol()
    branch = Reference(branch_id, 'Branch.id')

    transporter_id = IdCol(default=None)
    transporter = Reference(transporter_id, 'Transporter.id')

    purchase_orders = ReferenceSet('ReceivingOrder.id',
                                   'PurchaseReceivingMap.receiving_id',
                                   'PurchaseReceivingMap.purchase_id',
                                   'PurchaseOrder.id')

    def __init__(self, store=None, **kw):
        Domain.__init__(self, store=store, **kw)
        # These miss default parameters and needs to be set before
        # cfop, which triggers an implicit flush.
        self.branch = kw.pop('branch', None)
        self.supplier = kw.pop('supplier', None)
        if not 'cfop' in kw:
            self.cfop = sysparam.get_object(store, 'DEFAULT_RECEIVING_CFOP')

    #
    #  Public API
    #

    def confirm(self):
        for item in self.get_items():
            item.add_stock_items()

        purchases = list(self.purchase_orders)
        # XXX: Maybe FiscalBookEntry should not reference the payment group, but
        # lets keep this way for now until we refactor the fiscal book related
        # code, since it will pretty soon need a lot of changes.
        group = purchases[0].group
        FiscalBookEntry.create_product_entry(
            self.store,
            group, self.cfop, self.invoice_number,
            self.icms_total, self.ipi_total)

        self.invoice_total = self.total

        for purchase in purchases:
            if purchase.can_close():
                purchase.close()

    def add_purchase(self, order):
        return PurchaseReceivingMap(store=self.store, purchase=order,
                                    receiving=self)

    def add_purchase_item(self, item, quantity=None, batch_number=None,
                          parent_item=None):
        """Add a |purchaseitem| on this receiving order

        :param item: the |purchaseitem|
        :param decimal.Decimal quantity: the quantity of that item.
            If ``None``, it will be get from the item's pending quantity
        :param batch_number: a batch number that will be used to
            get or create a |batch| it will be get from the item's
            pending quantity or ``None`` if the item's |storable|
            is not controlling batches.
        :raises: :exc:`ValueError` when validating the quantity
            and testing the item's order for equality with :obj:`.order`
        """
        pending_quantity = item.get_pending_quantity()
        if quantity is None:
            quantity = pending_quantity

        if not (0 < quantity <= item.quantity):
            raise ValueError("The quantity must be higher than 0 and lower "
                             "than the purchase item's quantity")
        if quantity > pending_quantity:
            raise ValueError("The quantity must be lower than the item's "
                             "pending quantity")

        sellable = item.sellable
        storable = sellable.product_storable
        if batch_number is not None:
            batch = StorableBatch.get_or_create(self.store, storable=storable,
                                                batch_number=batch_number)
        else:
            batch = None

        self.validate_batch(batch, sellable)

        return ReceivingOrderItem(
            store=self.store,
            sellable=item.sellable,
            batch=batch,
            quantity=quantity,
            cost=item.cost,
            purchase_item=item,
            receiving_order=self,
            parent_item=parent_item)

    def update_payments(self, create_freight_payment=False):
        """Updates the payment value of all payments realated to this
        receiving. If create_freight_payment is set, a new payment will be
        created with the freight value. The other value as the surcharges and
        discounts will be included in the installments.

        :param create_freight_payment: True if we should create a new payment
                                       with the freight value, False otherwise.
        """
        difference = self.total - self.products_total
        if create_freight_payment:
            difference -= self.freight_total

        if difference != 0:
            # Get app pending payments for the purchases associated with this
            # receiving, and update them.
            payments = self.payments.find(status=Payment.STATUS_PENDING)
            payments_number = payments.count()
            if payments_number > 0:
                # XXX: There is a potential rounding error here.
                per_installments_value = difference / payments_number
                for payment in payments:
                    new_value = payment.value + per_installments_value
                    payment.update_value(new_value)

        if self.freight_total and create_freight_payment:
            self._create_freight_payment()

    def _create_freight_payment(self):
        store = self.store
        money_method = PaymentMethod.get_by_name(store, u'money')
        # If we have a transporter, the freight payment will be for him
        # (and in another payment group).
        purchases = list(self.purchase_orders)
        if len(purchases) == 1 and self.transporter is None:
            group = purchases[0].group
        else:
            if self.transporter:
                recipient = self.transporter.person
            else:
                recipient = self.supplier.person
            group = PaymentGroup(store=store, recipient=recipient)

        description = _(u'Freight for receiving %s') % (self.identifier, )
        payment = money_method.create_payment(
            Payment.TYPE_OUT,
            group, self.branch, self.freight_total,
            due_date=localnow(),
            description=description)
        payment.set_pending()
        return payment

    def get_items(self, with_children=True):
        store = self.store
        query = ReceivingOrderItem.receiving_order == self
        if not with_children:
            query = And(query, Eq(ReceivingOrderItem.parent_item_id, None))
        return store.find(ReceivingOrderItem, query)

    def remove_items(self):
        for item in self.get_items():
            item.receiving_order = None

    def remove_item(self, item):
        assert item.receiving_order == self
        type(item).delete(item.id, store=self.store)

    #
    # Properties
    #

    @property
    def payments(self):
        tables = [PurchaseReceivingMap, PurchaseOrder, Payment]
        query = And(PurchaseReceivingMap.receiving_id == self.id,
                    PurchaseReceivingMap.purchase_id == PurchaseOrder.id,
                    Payment.group_id == PurchaseOrder.group_id)
        return self.store.using(tables).find(Payment, query)

    @property
    def supplier_name(self):
        if not self.supplier:
            return u""
        return self.supplier.get_description()

    #
    # Accessors
    #

    @property
    def cfop_code(self):
        return self.cfop.code.encode()

    @property
    def transporter_name(self):
        if not self.transporter:
            return u""
        return self.transporter.get_description()

    @property
    def branch_name(self):
        return self.branch.get_description()

    @property
    def responsible_name(self):
        return self.responsible.get_description()

    @property
    def products_total(self):
        total = sum([item.get_total() for item in self.get_items()],
                    currency(0))
        return currency(total)

    @property
    def receival_date_str(self):
        return self.receival_date.strftime("%x")

    @property
    def total_surcharges(self):
        """Returns the sum of all surcharges (purchase & receiving)"""
        total_surcharge = 0
        if self.surcharge_value:
            total_surcharge += self.surcharge_value
        if self.secure_value:
            total_surcharge += self.secure_value
        if self.expense_value:
            total_surcharge += self.expense_value

        for purchase in self.purchase_orders:
            total_surcharge += purchase.surcharge_value

        if self.ipi_total:
            total_surcharge += self.ipi_total

        # CIF freights don't generate payments.
        if (self.freight_total and
            self.freight_type not in (self.FREIGHT_CIF_UNKNOWN,
                                      self.FREIGHT_CIF_INVOICE)):
            total_surcharge += self.freight_total

        return currency(total_surcharge)

    @property
    def total_discounts(self):
        """Returns the sum of all discounts (purchase & receiving)"""
        total_discount = 0
        if self.discount_value:
            total_discount += self.discount_value

        for purchase in self.purchase_orders:
            total_discount += purchase.discount_value

        return currency(total_discount)

    @property
    def total(self):
        """Fetch the total, including discount and surcharge for both the
        purchase order and the receiving order.
        """
        total = self.products_total
        total -= self.total_discounts
        total += self.total_surcharges

        return currency(total)

    def guess_freight_type(self):
        """Returns a freight_type based on the purchase's freight_type"""
        purchases = list(self.purchase_orders)
        assert len(purchases) == 1

        purchase = purchases[0]
        if purchase.freight_type == PurchaseOrder.FREIGHT_FOB:
            if purchase.is_paid():
                freight_type = ReceivingOrder.FREIGHT_FOB_PAYMENT
            else:
                freight_type = ReceivingOrder.FREIGHT_FOB_INSTALLMENTS
        elif purchase.freight_type == PurchaseOrder.FREIGHT_CIF:
            if purchase.expected_freight:
                freight_type = ReceivingOrder.FREIGHT_CIF_INVOICE
            else:
                freight_type = ReceivingOrder.FREIGHT_CIF_UNKNOWN

        return freight_type

    def _get_percentage_value(self, percentage):
        if not percentage:
            return currency(0)
        subtotal = self.products_total
        percentage = Decimal(percentage)
        return subtotal * (percentage / 100)

    @property
    def discount_percentage(self):
        discount_value = self.discount_value
        if not discount_value:
            return currency(0)
        subtotal = self.products_total
        assert subtotal > 0, (u'the subtotal should not be zero '
                              u'at this point')
        total = subtotal - discount_value
        percentage = (1 - total / subtotal) * 100
        return quantize(percentage)

    @discount_percentage.setter
    def discount_percentage(self, value):
        """Discount by percentage.
        Note that percentage must be added as an absolute value not as a
        factor like 1.05 = 5 % of surcharge
        The correct form is 'percentage = 3' for a discount of 3 %
        """
        self.discount_value = self._get_percentage_value(value)

    @property
    def surcharge_percentage(self):
        """Surcharge by percentage.
        Note that surcharge must be added as an absolute value not as a
        factor like 0.97 = 3 % of discount.
        The correct form is 'percentage = 3' for a surcharge of 3 %
        """
        surcharge_value = self.surcharge_value
        if not surcharge_value:
            return currency(0)
        subtotal = self.products_total
        assert subtotal > 0, (u'the subtotal should not be zero '
                              u'at this point')
        total = subtotal + surcharge_value
        percentage = ((total / subtotal) - 1) * 100
        return quantize(percentage)

    @surcharge_percentage.setter
    def surcharge_percentage(self, value):
        self.surcharge_value = self._get_percentage_value(value)


class PurchaseReceivingMap(Domain):
    """This class stores a map for purchase and receivings.

    One purchase may be received more than once, for instance, if it was
    shippped in more than one package.

    Also, a receiving may be for different purchase orders, if more than one
    purchase order was shipped in the same package.
    """

    __storm_table__ = 'purchase_receiving_map'

    purchase_id = IdCol()

    #: The purchase that was recieved
    purchase = Reference(purchase_id, 'PurchaseOrder.id')

    receiving_id = IdCol()

    #: In which receiving the purchase was received.
    receiving = Reference(receiving_id, 'ReceivingOrder.id')
