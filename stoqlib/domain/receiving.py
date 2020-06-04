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

import collections
from decimal import Decimal

from kiwi.currency import currency
from storm.expr import And, Eq
from storm.references import Reference, ReferenceSet

from stoqlib.database.properties import (PriceCol, QuantityCol, IntCol,
                                         DateTimeCol, UnicodeCol, IdentifierCol,
                                         IdCol, EnumCol)
from stoqlib.domain.base import Domain, IdentifiableDomain
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import LoginUser
from stoqlib.domain.product import (ProductHistory, StockTransactionHistory,
                                    StorableBatch)
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.stockdecrease import StockDecreaseItem
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

    #: The ICMS ST value for the product purchased
    icms_st_value = PriceCol(default=0)

    #: The IPI value for the product purchased
    ipi_value = PriceCol(default=0)

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

    @property
    def returned_quantity(self):
        return self.store.find(StockDecreaseItem, receiving_order_item=self).sum(
            StockDecreaseItem.quantity) or Decimal('0')

    @property
    def purchase_cost(self):
        return self.purchase_item.cost

    @property
    def description(self):
        return self.sellable.description

    @property
    def cost_with_ipi(self):
        return currency(quantize(self.cost + self.unit_ipi_value))

    @property
    def unit_ipi_value(self):
        """The Ipi value must be shared through the items"""
        return currency(quantize(self.ipi_value / self.quantity))
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
        return currency(quantize(self.quantity * cost))

    def get_total_with_ipi(self):
        cost = self.purchase_item.cost
        ipi_value = self.ipi_value
        return currency(quantize(self.quantity * cost + ipi_value))

    def get_received_total(self, with_ipi=False):

        ipi = self.ipi_value if with_ipi else 0
        return currency(quantize((self.quantity * self.cost) + ipi))

    def get_quantity_unit_string(self):
        unit = self.sellable.unit
        data = u"%s %s" % (self.quantity,
                           unit and unit.description or u"")
        # The unit may be empty
        return data.strip()

    def add_stock_items(self, user: LoginUser):
        """This is normally called from ReceivingOrder when
        a the receving order is confirmed.
        """
        store = self.store
        if not self.sellable.product.manage_stock:
            return

        if self.quantity > self.get_remaining_quantity():
            raise ValueError(
                u"Quantity received (%d) is greater than "
                u"quantity ordered (%d)" % (self.quantity,
                                            self.get_remaining_quantity()))

        branch = self.receiving_order.branch
        storable = self.sellable.product_storable
        purchase = self.purchase_item.order
        if storable is not None:
            cost = self.cost + (self.ipi_value / self.quantity)
            storable.increase_stock(self.quantity, branch,
                                    StockTransactionHistory.TYPE_RECEIVED_PURCHASE,
                                    self.id, user, cost, batch=self.batch)
        purchase.increase_quantity_received(self.purchase_item, self.quantity)
        ProductHistory.add_received_item(store, branch, self)

    def is_totally_returned(self):
        children = self.children_items
        if children.count():
            return all(child.quantity == child.returned_quantity for child in
                       children)

        return self.quantity == self.returned_quantity

    def get_receiving_packing_number(self):
        return self.receiving_order.packing_number


class ReceivingOrder(IdentifiableDomain):
    """Receiving order definition.
    """

    __storm_table__ = 'receiving_order'

    #: Products in the order was not received or received partially.
    STATUS_PENDING = u'pending'

    #: All products in the order has been received then the order is closed.
    STATUS_CLOSED = u'closed'

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

    #: The invoice number of the order that has been received.
    invoice_number = IntCol()

    # Número do Romaneio. The number used by the transporter to identify the packing
    packing_number = UnicodeCol()

    cfop_id = IdCol()
    cfop = Reference(cfop_id, 'CfopData.id')

    responsible_id = IdCol()
    responsible = Reference(responsible_id, 'LoginUser.id')

    branch_id = IdCol()
    branch = Reference(branch_id, 'Branch.id')

    station_id = IdCol(allow_none=False)
    #: The station this object was created at
    station = Reference(station_id, 'BranchStation.id')

    receiving_invoice_id = IdCol(default=None)
    receiving_invoice = Reference(receiving_invoice_id, 'ReceivingInvoice.id')

    purchase_orders = ReferenceSet('ReceivingOrder.id',
                                   'PurchaseReceivingMap.receiving_id',
                                   'PurchaseReceivingMap.purchase_id',
                                   'PurchaseOrder.id')

    def __init__(self, store=None, **kw):
        super(ReceivingOrder, self).__init__(store=store, **kw)
        # These miss default parameters and needs to be set before
        # cfop, which triggers an implicit flush.
        self.branch = kw.pop('branch', None)
        if not 'cfop' in kw:
            self.cfop = sysparam.get_object(store, 'DEFAULT_RECEIVING_CFOP')

    #
    #  Public API
    #

    def confirm(self, user: LoginUser):
        if self.receiving_invoice:
            self.receiving_invoice.confirm(user)

        for item in self.get_items():
            item.add_stock_items(user)

        purchases = list(self.purchase_orders)
        for purchase in purchases:
            if purchase.can_close():
                purchase.close()

        # XXX: Will the packing number aways be the same as the suppliert order?
        if purchase.work_order:
            self.packing_number = purchase.work_order.supplier_order

    def add_purchase(self, order):
        return PurchaseReceivingMap(store=self.store, purchase=order,
                                    receiving=self)

    def add_purchase_item(self, item, quantity=None, batch_number=None,
                          parent_item=None, ipi_value=0, icms_st_value=0):
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
            ipi_value=ipi_value,
            icms_st_value=icms_st_value,
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
        # If the invoice has more than one receiving, the values could be inconsistent
        assert self.receiving_invoice.receiving_orders.count() == 1
        difference = self.receiving_invoice.total - self.receiving_invoice.products_total
        if create_freight_payment:
            difference -= self.receiving_invoice.freight_total

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

        if self.receiving_invoice.freight_total and create_freight_payment:
            purchases = list(self.purchase_orders)
            if len(purchases) == 1 and self.receiving_invoice.transporter is None:
                group = purchases[0].group
            else:
                group = None
            self.receiving_invoice.create_freight_payment(group=group)

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

    def is_totally_returned(self):
        return all(item.is_totally_returned() for item in self.get_items())

    #
    # Properties
    #

    @property
    def payments(self):
        if self.receiving_invoice and self.receiving_invoice.group:
            return self.receiving_invoice.payments

        tables = [PurchaseReceivingMap, PurchaseOrder, Payment]
        query = And(PurchaseReceivingMap.receiving_id == self.id,
                    PurchaseReceivingMap.purchase_id == PurchaseOrder.id,
                    Payment.group_id == PurchaseOrder.group_id)
        return self.store.using(tables).find(Payment, query)

    #
    # Accessors
    #

    @property
    def cfop_code(self):
        return self.cfop.code

    @property
    def freight_type(self):
        if self.receiving_invoice:
            return self.receiving_invoice.freight_type
        return None

    @property
    def branch_name(self):
        return self.branch.get_description()

    @property
    def responsible_name(self):
        return self.responsible.get_description()

    @property
    def products_total(self):
        total = sum((item.get_received_total() for item in self.get_items()), currency(0))
        return currency(total)

    @property
    def product_total_with_ipi(self):
        total = sum((item.get_received_total(with_ipi=True)
                     for item in self.get_items()), currency(0))
        return currency(total)

    @property
    def receival_date_str(self):
        return self.receival_date.strftime("%x")

    @property
    def total_surcharges(self):
        """Returns the sum of all surcharges (purchase & receiving)"""
        total_surcharge = 0
        for purchase in self.purchase_orders:
            total_surcharge += purchase.surcharge_value
        return currency(total_surcharge)

    @property
    def total_quantity(self):
        """Returns the sum of all received quantities"""
        return sum(item.quantity for item in self.get_items(with_children=False))

    @property
    def total_discounts(self):
        """Returns the sum of all discounts (purchase & receiving)"""
        total_discount = 0
        for purchase in self.purchase_orders:
            total_discount += purchase.discount_value
        return currency(total_discount)

    @property
    def total(self):
        """Fetch the total, including discount and surcharge for purchase order
        """
        total = self.product_total_with_ipi
        total -= self.total_discounts
        total += self.total_surcharges

        return currency(total)


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


class ReceivingInvoice(IdentifiableDomain):

    __storm_table__ = 'receiving_invoice'

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
    icms_st_total = PriceCol(default=0)
    ipi_total = PriceCol(default=0)

    #: The invoice number of the order that has been received.
    invoice_number = IntCol()

    #: The invoice total value of the order received
    invoice_total = PriceCol(default=0)

    #: The invoice key of the order received
    invoice_key = UnicodeCol()

    responsible_id = IdCol()
    responsible = Reference(responsible_id, 'LoginUser.id')

    branch_id = IdCol()
    branch = Reference(branch_id, 'Branch.id')

    station_id = IdCol(allow_none=False)
    #: The station this object was created at
    station = Reference(station_id, 'BranchStation.id')

    supplier_id = IdCol()
    supplier = Reference(supplier_id, 'Supplier.id')

    transporter_id = IdCol()
    transporter = Reference(transporter_id, 'Transporter.id')

    group_id = IdCol()
    group = Reference(group_id, 'PaymentGroup.id')

    receiving_orders = ReferenceSet('id', 'ReceivingOrder.receiving_invoice_id')

    @classmethod
    def check_unique_invoice_number(cls, store, invoice_number, supplier):
        count = store.find(cls, And(cls.invoice_number == invoice_number,
                                    ReceivingInvoice.supplier == supplier)).count()
        return count == 0

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
        if self.ipi_total:
            total_surcharge += self.ipi_total
        if self.icms_st_total:
            total_surcharge += self.icms_st_total

        for receiving in self.receiving_orders:
            total_surcharge += receiving.total_surcharges

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

        for receiving in self.receiving_orders:
            total_discount += receiving.total_discounts

        return currency(total_discount)

    @property
    def products_total(self):
        return currency(sum((r.products_total for r in self.receiving_orders), 0))

    @property
    def total(self):
        """Fetch the total, including discount and surcharge for both the
        purchase order and the receiving order.
        """
        total = self.products_total
        total -= self.total_discounts
        total += self.total_surcharges
        return currency(total)

    @property
    def total_for_payment(self):
        """Fetch the total for the invoice payment. Exclude the freight value if
        it will be in a diferent pament
        """
        total = self.total
        if self.freight_type == self.FREIGHT_FOB_PAYMENT:
            total -= self.freight_total
        return currency(total)

    @property
    def payments(self):
        """Returns all valid payments for this invoice

        This will return a list of valid payments for this invoice, that
        is, all payments on the payment group that were not cancelled.
        If you need to get the cancelled too, use self.group.payments.

        :returns: a list of |payment|
        """
        return self.group.get_valid_payments()

    @property
    def supplier_name(self):
        if not self.supplier:
            return u""
        return self.supplier.get_description()

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

    def create_freight_payment(self, group=None):
        store = self.store
        money_method = PaymentMethod.get_by_name(store, u'money')
        # If we have a transporter, the freight payment will be for him
        if not group:
            if self.transporter:
                recipient = self.transporter.person
            else:
                recipient = self.supplier.person
            group = PaymentGroup(store=store, recipient=recipient)

        description = _(u'Freight for receiving %s') % (self.identifier, )
        payment = money_method.create_payment(
            self.branch, self.station,
            Payment.TYPE_OUT,
            group, self.freight_total,
            due_date=localnow(),
            description=description)
        payment.set_pending()
        return payment

    def guess_freight_type(self):
        """Returns a freight_type based on the purchase's freight_type"""
        purchases = list(self.get_purchase_orders())
        assert len(purchases) == 1

        purchase = purchases[0]
        if purchase.freight_type == PurchaseOrder.FREIGHT_FOB:
            if purchase.is_paid():
                freight_type = ReceivingInvoice.FREIGHT_FOB_PAYMENT
            else:
                freight_type = ReceivingInvoice.FREIGHT_FOB_INSTALLMENTS
        elif purchase.freight_type == PurchaseOrder.FREIGHT_CIF:
            if purchase.expected_freight:
                freight_type = ReceivingInvoice.FREIGHT_CIF_INVOICE
            else:
                freight_type = ReceivingInvoice.FREIGHT_CIF_UNKNOWN

        return freight_type

    def confirm(self, user: LoginUser):
        self.invoice_total = self.total
        if self.group:
            self.group.confirm()
        for receiving in self.receiving_orders:
            receiving.invoice_number = self.invoice_number

        # XXX: Maybe FiscalBookEntry should not reference the payment group, but
        # lets keep this way for now until we refactor the fiscal book related
        # code, since it will pretty soon need a lot of changes.
        group = self.group or self.get_purchase_orders().pop().group
        FiscalBookEntry.create_product_entry(
            self.store, self.branch, user, group, receiving.cfop, self.invoice_number,
            self.icms_total, self.ipi_total)

    def add_receiving(self, receiving):
        receiving.receiving_invoice = self

    def get_purchase_orders(self):
        purchases = set()
        for receiving in self.receiving_orders:
            purchases.update(set(receiving.purchase_orders))
        return purchases

    def _get_percentage_value(self, percentage):
        if not percentage:
            return currency(0)
        subtotal = self.products_total
        percentage = Decimal(percentage)
        return subtotal * (percentage / 100)
