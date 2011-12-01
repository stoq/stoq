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

import datetime
from decimal import Decimal

from kiwi.argcheck import argcheck
from kiwi.datatypes import currency

from stoqlib.database.orm import PriceCol, QuantityCol
from stoqlib.database.orm import ForeignKey, IntCol, DateTimeCol, UnicodeCol
from stoqlib.domain.base import Domain
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.product import ProductHistory
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.lib.defaults import quantize
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ReceivingOrderItem(Domain):
    """This class stores information of the purchased items.

    B{Importante attributes}
        - I{quantity}: the total quantity received for a certain
          product
        - I{cost}: the cost for each product received
    """
    quantity = QuantityCol()
    cost = PriceCol()
    purchase_item = ForeignKey('PurchaseItem')
    sellable = ForeignKey('Sellable')
    receiving_order = ForeignKey('ReceivingOrder')

    #
    # Accessors
    #

    def get_remaining_quantity(self):
        """Get the remaining quantity from the purchase order this item
        is included in.
        @returns: the remaining quantity
        """
        return self.purchase_item.get_pending_quantity()

    def get_total(self):
        # We need to use the the purchase_item cost, since the current cost
        # might be different.
        cost = self.purchase_item.cost
        return currency(self.quantity * cost)

    def get_quantity_unit_string(self):
        unit = self.sellable.unit
        return "%s %s" % (self.quantity,
                          unit and unit.description or u"")

    def get_unit_description(self):
        unit = self.sellable.unit
        return "%s" % (unit and unit.description or "")

    def add_stock_items(self):
        """This is normally called from ReceivingOrder when
        a the receving order is confirmed.
        """
        conn = self.get_connection()
        if self.quantity > self.get_remaining_quantity():
            raise ValueError(
                "Quantity received (%d) is greater than "
                "quantity ordered (%d)" % (
                self.quantity,
                self.get_remaining_quantity()))

        branch = self.receiving_order.branch
        storable = IStorable(self.sellable.product, None)
        if storable is not None:
            storable.increase_stock(self.quantity, branch, self.cost)
        purchase = self.purchase_item.order
        purchase.increase_quantity_received(self.purchase_item, self.quantity)
        ProductHistory.add_received_item(conn, branch, self)


class ReceivingOrder(Domain):
    """Receiving order definition.

    @cvar STATUS_PENDING: Products in the order was not received
      or received partially.
    @cvar STATUS_CLOSED: All products in the order has been received then
        the order is closed.
    @ivar status: status of the order
    @ivar receival_date: Date that order has been closed.
    @ivar confirm_date: Date that order was send to Stock application.
    @ivar notes: Some optional additional information related to this order.
    @ivar freight_type: Type of freight
    @ivar freight_total: Total of freight paid in receiving order.
    @ivar surcharge_value:
    @ivar discount_value: Discount value in receiving order's payment.
    @ivar secure_value: Secure value paid in receiving order's payment.
    @ivar expense_value: Other expenditures paid in receiving order's payment.
    @ivar invoice_number: The number of the order that has been received.
    """

    (STATUS_PENDING,
     STATUS_CLOSED) = range(2)

    (FREIGHT_FOB_PAYMENT,
     FREIGHT_FOB_INSTALLMENTS,
     FREIGHT_CIF_UNKNOWN,
     FREIGHT_CIF_INVOICE) = range(4)

    freight_types = {FREIGHT_FOB_PAYMENT: _(u"FOB - Freight value "
                                            "on a new payment"),
                     FREIGHT_FOB_INSTALLMENTS: _(u"FOB - Freight value "
                                                 "on installments"),
                     FREIGHT_CIF_UNKNOWN: _(u"CIF - Freight value is unknown"),
                     FREIGHT_CIF_INVOICE: _(u"CIF - Freight value highlighted "
                                            "on invoice")}

    FOB_FREIGHTS = (FREIGHT_FOB_PAYMENT,
                    FREIGHT_FOB_INSTALLMENTS, )
    CIF_FREIGHTS = (FREIGHT_CIF_UNKNOWN,
                    FREIGHT_CIF_INVOICE)

    status = IntCol(default=STATUS_PENDING)
    receival_date = DateTimeCol(default=datetime.datetime.now)
    confirm_date = DateTimeCol(default=None)
    notes = UnicodeCol(default='')
    freight_type = IntCol(default=FREIGHT_FOB_PAYMENT)
    freight_total = PriceCol(default=0)
    surcharge_value = PriceCol(default=0)
    discount_value = PriceCol(default=0)
    secure_value = PriceCol(default=0)
    expense_value = PriceCol(default=0)

    # This is Brazil-specific information
    icms_total = PriceCol(default=0)
    ipi_total = PriceCol(default=0)
    invoice_number = IntCol()
    invoice_total = PriceCol(default=None)
    cfop = ForeignKey("CfopData")

    responsible = ForeignKey('PersonAdaptToUser')
    supplier = ForeignKey('PersonAdaptToSupplier')
    branch = ForeignKey('PersonAdaptToBranch')
    purchase = ForeignKey('PurchaseOrder')
    transporter = ForeignKey('PersonAdaptToTransporter', default=None)

    def _create(self, id, **kw):
        conn = self.get_connection()
        if not 'cfop' in kw:
            conn.block_implicit_flushes()
            kw['cfop'] = sysparam(conn).DEFAULT_RECEIVING_CFOP
            conn.unblock_implicit_flushes()
        Domain._create(self, id, **kw)

    def confirm(self):
        for item in self.get_items():
            item.add_stock_items()

        FiscalBookEntry.create_product_entry(
            self.get_connection(),
            self.purchase.group, self.cfop, self.invoice_number,
            self.icms_total, self.ipi_total)
        self.invoice_total = self.get_total()
        if self.purchase.can_close():
            self.purchase.close()

    def update_payments(self, create_freight_payment=False):
        """Updates the payment value of all payments realated to this
        receiving. If create_freight_payment is set, a new payment will be
        created with the freight value. The other value as the surcharges and
        discounts will be included in the installments.

        @param create_freight_payment: True if we should create a new payment
                                       with the freight value, False otherwise.
        """
        group = self.purchase.group
        difference = self.get_total() - self.get_products_total()
        if create_freight_payment:
            difference -= self.freight_total

        if difference != 0:
            payments = group.get_pending_payments()
            payments_number = payments.count()
            if payments_number > 0:
                per_installments_value = difference / payments_number
                for payment in payments:
                    new_value = payment.value + per_installments_value
                    payment.update_value(new_value)

        if self.freight_total and create_freight_payment:
            self._create_freight_payment()

    def _create_freight_payment(self):
        register_payment_operations()

        conn = self.get_connection()
        money_method = PaymentMethod.get_by_name(conn, 'money')
        # If we have a transporter, the freight payment will be for him
        # (and in another payment group).
        if self.transporter is not None:
            group = PaymentGroup(connection=conn)
            group.recipient = self.transporter.person
        else:
            group = self.purchase.group

        description = _(u'Freight for purchase %s') % (
                        self.purchase.get_order_number_str(), )
        out_payment = money_method.create_outpayment(
            group, self.freight_total,
            due_date=datetime.datetime.today(),
            description=description)
        payment = out_payment.get_adapted()
        payment.set_pending()
        return payment

    def get_items(self):
        conn = self.get_connection()
        return ReceivingOrderItem.selectBy(receiving_order=self,
                                           connection=conn)

    def remove_items(self):
        for item in self.get_items():
            item.receiving_order = None

    def remove_item(self, item):
        assert item.receiving_order == self
        type(item).delete(item.id, connection=self.get_connection())

    #
    # Properties
    #

    @property
    def receiving_number(self):
        return self.id

    @property
    def group(self):
        return self.purchase.group

    @property
    def payments(self):
        return self.group.payments

    #
    # Accessors
    #

    def get_cfop_code(self):
        return self.cfop.code.encode()

    def get_transporter_name(self):
        if not self.transporter:
            return u""
        return self.transporter.get_description()

    def get_receiving_number_str(self):
        return u"%04d" % self.id

    def get_branch_name(self):
        return self.branch.get_description()

    def get_supplier_name(self):
        if not self.supplier:
            return u""
        return self.supplier.get_description()

    def get_responsible_name(self):
        return self.responsible.get_description()

    def get_products_total(self):
        total = sum([item.get_total() for item in self.get_items()],
                     currency(0))
        return currency(total)

    def get_order_number(self):
        return self.purchase.get_order_number_str()

    def get_receival_date_str(self):
        return self.receival_date.strftime("%x")

    def _get_total_surcharges(self):
        """Returns the sum of all surcharges (purchase & receiving)"""
        total_surcharge = 0
        if self.surcharge_value:
            total_surcharge += self.surcharge_value
        if self.secure_value:
            total_surcharge += self.secure_value
        if self.expense_value:
            total_surcharge += self.expense_value

        if self.purchase.surcharge_value:
            total_surcharge += self.purchase.surcharge_value

        if self.ipi_total:
            total_surcharge += self.ipi_total

        # CIF freights don't generate payments.
        if (self.freight_total and
            self.freight_type not in (self.FREIGHT_CIF_UNKNOWN,
                                      self.FREIGHT_CIF_INVOICE)):
            total_surcharge += self.freight_total

        return currency(total_surcharge)

    def _get_total_discounts(self):
        """Returns the sum of all discounts (purchase & receiving)"""
        total_discount = 0
        if self.discount_value:
            total_discount += self.discount_value

        if self.purchase.discount_value:
            total_discount += self.purchase.discount_value

        return currency(total_discount)

    def get_total(self):
        """Fetch the total, including discount and surcharge for both the
        purchase order and the receiving order.
        """

        total = self.get_products_total()
        total -= self._get_total_discounts()
        total += self._get_total_surcharges()

        return currency(total)

    def guess_freight_type(self):
        """Returns a freight_type based on the purchase's freight_type"""
        if self.purchase.freight_type == PurchaseOrder.FREIGHT_FOB:
            if self.purchase.is_paid():
                freight_type = ReceivingOrder.FREIGHT_FOB_PAYMENT
            else:
                freight_type = ReceivingOrder.FREIGHT_FOB_INSTALLMENTS
        elif self.purchase.freight_type == PurchaseOrder.FREIGHT_CIF:
            if not self.purchase.expected_freight:
                freight_type = ReceivingOrder.FREIGHT_CIF_UNKNOWN
            else:
                freight_type = ReceivingOrder.FREIGHT_CIF_INVOICE

        return freight_type

    def _get_percentage_value(self, percentage):
        if not percentage:
            return currency(0)
        subtotal = self.get_products_total()
        percentage = Decimal(percentage)
        return subtotal * (percentage / 100)

    def _set_discount_by_percentage(self, value):
        """Sets a discount by percentage.
        Note that percentage must be added as an absolute value not as a
        factor like 1.05 = 5 % of surcharge
        The correct form is 'percentage = 3' for a discount of 3 %
        """
        self.discount_value = self._get_percentage_value(value)

    def _get_discount_by_percentage(self):
        discount_value = self.discount_value
        if not discount_value:
            return currency(0)
        subtotal = self.get_products_total()
        assert subtotal > 0, ('the subtotal should not be zero '
                              'at this point')
        total = subtotal - discount_value
        percentage = (1 - total / subtotal) * 100
        return quantize(percentage)

    discount_percentage = property(_get_discount_by_percentage,
                                   _set_discount_by_percentage)

    def _set_surcharge_by_percentage(self, value):
        """Sets a surcharge by percentage.
        Note that surcharge must be added as an absolute value not as a
        factor like 0.97 = 3 % of discount.
        The correct form is 'percentage = 3' for a surcharge of 3 %
        """
        self.surcharge_value = self._get_percentage_value(value)

    def _get_surcharge_by_percentage(self):
        surcharge_value = self.surcharge_value
        if not surcharge_value:
            return currency(0)
        subtotal = self.get_products_total()
        assert subtotal > 0, ('the subtotal should not be zero '
                              'at this point')
        total = subtotal + surcharge_value
        percentage = ((total / subtotal) - 1) * 100
        return quantize(percentage)

    surcharge_percentage = property(_get_surcharge_by_percentage,
                                    _set_surcharge_by_percentage)


@argcheck(PurchaseOrder, ReceivingOrder)
def get_receiving_items_by_purchase_order(purchase_order, receiving_order):
    """Returns a list of receiving items based on a list of purchase items
    that weren't received yet.

    @param purchase_order: a PurchaseOrder instance that holds one or more
                           purchase items
    @param receiving_order: a ReceivingOrder instance tied with the
                            receiving_items that will be created
    """
    conn = purchase_order.get_connection()
    return [ReceivingOrderItem(connection=conn,
                               quantity=item.get_pending_quantity(),
                               cost=item.cost,
                               sellable=item.sellable,
                               purchase_item=item,
                               receiving_order=receiving_order)
            for item in purchase_order.get_pending_items()]
