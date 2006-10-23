# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Purchase management """

from decimal import Decimal
from datetime import datetime

from kiwi.argcheck import argcheck
from kiwi.datatypes import currency
from zope.interface import implements

from sqlobject import (ForeignKey, IntCol, DateTimeCol, UnicodeCol,
                       SQLObject)

from stoqlib.database.columns import PriceCol, DecimalCol, AutoIncCol
from stoqlib.exceptions import DatabaseInconsistency, StoqlibError
from stoqlib.lib.defaults import (METHOD_CHECK, METHOD_BILL,
                                  METHOD_MONEY)
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.base import Domain, BaseSQLView
from stoqlib.domain.payment.base import AbstractPaymentGroup
from stoqlib.domain.interfaces import (ICheckPM, IBillPM, IMoneyPM,
                                       IPaymentGroup, IContainer)
from stoqlib.lib.validators import format_quantity

_ = stoqlib_gettext


class PurchaseItem(Domain):
    """This class stores information of the purchased items.

    B{Importante attributes}
        - I{base_cost}: the cost which helps the purchaser to define the
                        main cost of a certain product.
    """
    quantity = DecimalCol(default=1)
    quantity_received = DecimalCol(default=0)
    base_cost = PriceCol()
    cost = PriceCol()
    sellable = ForeignKey('ASellable')
    order = ForeignKey('PurchaseOrder')

    def _create(self, id, **kw):
        if 'base_cost' in kw:
            raise TypeError('You should not provide a base_cost'
                            'argument since it is set automatically')
        if not 'sellable' in kw:
            raise TypeError('You must provide a sellable argument')
        if not 'order' in kw:
            raise TypeError('You must provide a order argument')

        kw['base_cost'] = kw['sellable'].cost

        if not 'cost' in kw:
            kw['cost'] = kw['sellable'].cost

        if kw['sellable'].id in [item.sellable.id
                                   for item in kw['order'].get_items()]:
            raise ValueError('This product was already added to the order')
        Domain._create(self, id, **kw)

    #
    # Accessors
    #

    def get_total(self):
        return currency(self.quantity * self.cost)

    def get_received_total(self):
        return currency(self.quantity_received * self.cost)

    def has_been_received(self):
        return self.quantity_received >= self.quantity

    def get_pending_quantity(self):
        if not self.has_been_received:
            return Decimal(0)
        return self.quantity - self.quantity_received

    def get_quantity_as_string(self):
        unit = self.sellable.unit
        return "%s %s" % (format_quantity(self.quantity),
                          unit and unit.description or u"")

    def get_quantity_received_as_string(self):
        unit = self.sellable.unit
        return "%s %s" % (format_quantity(self.quantity_received),
                          unit and unit.description or u"")

class PurchaseOrder(Domain):
    """Purchase and order definition."""

    implements(IContainer)

    (ORDER_CANCELLED,
     ORDER_QUOTING,
     ORDER_PENDING,
     ORDER_CONFIRMED,
     ORDER_CLOSED) = range(5)

    statuses = {ORDER_CANCELLED:    _(u'Cancelled'),
                ORDER_QUOTING:      _(u'Quoting'),
                ORDER_PENDING:      _(u'Pending'),
                ORDER_CONFIRMED:    _(u'Confirmed'),
                ORDER_CLOSED:       _(u'Closed')}

    (FREIGHT_FOB,
     FREIGHT_CIF) = range(2)

    freight_types = {FREIGHT_FOB    : _(u'FOB'),
                     FREIGHT_CIF    : _(u'CIF')}

    status = IntCol(default=ORDER_QUOTING)
    order_number = AutoIncCol('stoqlib_purchase_ordernumber_seq')
    open_date = DateTimeCol(default=datetime.now)
    quote_deadline = DateTimeCol(default=None)
    expected_receival_date = DateTimeCol(default=datetime.now)
    expected_pay_date = DateTimeCol(default=None)
    receival_date = DateTimeCol(default=None)
    confirm_date = DateTimeCol(default=None)
    notes = UnicodeCol(default='')
    salesperson_name = UnicodeCol(default='')
    freight_type = IntCol(default=FREIGHT_FOB)
    freight = DecimalCol(default=0)
    surcharge_value = PriceCol(default=0)
    discount_value = PriceCol(default=0)
    supplier = ForeignKey('PersonAdaptToSupplier')
    branch = ForeignKey('PersonAdaptToBranch')
    transporter = ForeignKey('PersonAdaptToTransporter', default=None)

    #
    # IContainer Implementation
    #

    def get_items(self):
        return PurchaseItem.selectBy(order=self,
                                     connection=self.get_connection())

    @argcheck(PurchaseItem)
    def remove_item(self, item):
        conn = self.get_connection()
        if item.order is not self:
            raise ValueError('Argument item must have an order attribute '
                             'associated with the current purchase instance')
        PurchaseItem.delete(item.id, connection=conn)

    def add_item(self, sellable, quantity=Decimal(1)):
        conn = self.get_connection()
        return PurchaseItem(connection=conn, order=self,
                            sellable=sellable, quantity=quantity)

    #
    # SQLObject hooks
    #

    def _create(self, id, **kw):
        # Purchase objects must be set as valid explicitly
        kw['_is_valid_model'] = False
        Domain._create(self, id, **kw)

    #
    # General methods
    #

    def receive_item(self, item, quantity_to_receive):
        if not item in self.get_pending_items():
            raise StoqlibError('This item is not pending, hence '
                               'cannot be received')
        quantity = item.quantity - item.quantity_received
        if quantity < quantity_to_receive:
            raise StoqlibError('The quantity that you want to receive '
                               'is greater than the total quantity of '
                               'this item %r' % item)
        self.increase_quantity_received(item.sellable,
                                        quantity_to_receive)

    def confirm_order(self, confirm_date=datetime.now()):
        if self.status != self.ORDER_PENDING:
            raise ValueError('Invalid order status, it should be '
                             'ORDER_PENDING, got %s'
                             % self.get_status_str())
        conn = self.get_connection()
        if sysparam(conn).USE_PURCHASE_PREVIEW_PAYMENTS:
            group = IPaymentGroup(self, None)
            if not group:
                raise ValueError('You must have a IPaymentGroup facet '
                                 'defined at this point')
            base_method = sysparam(conn).BASE_PAYMENT_METHOD
            total = self.get_purchase_total()
            self._create_preview_outpayments(conn, group, base_method, total)
        self.status = self.ORDER_CONFIRMED
        self.confirm_date = confirm_date

    def _create_preview_outpayments(self, conn, group, base_method, total):

        # FIXME: Move this special cased logic to the specific
        #        implementation of each payment method
        if group.default_method == METHOD_MONEY:
            method = IMoneyPM(base_method)
            method.setup_outpayments(total, group,
                                     group.installments_number)
            return
        elif group.default_method == METHOD_CHECK:
            method = ICheckPM(base_method)
        elif group.default_method == METHOD_BILL:
            method = IBillPM(base_method)
        else:
            raise ValueError('Invalid payment method, got %d' %
                             group.default_method)

        method.setup_outpayments(group, group.installments_number,
                                 self.expected_receival_date,
                                 group.interval_type,
                                 group.intervals, total)

    def _get_percentage_value(self, percentage):
        if not percentage:
            return currency(0)
        subtotal = self.get_purchase_subtotal()
        percentage = Decimal(str(percentage))
        return subtotal * (percentage / 100)

    def _set_discount_by_percentage(self, value):
        """Sets a discount by percentage.
        Note that percentage must be added as an absolute value not as a
        factor like 1.05 = 5 % of surcharge
        The correct form is 'percentage = 3' for a discount of 3 %"""
        self.discount_value = self._get_percentage_value(value)

    def _get_discount_by_percentage(self):
        discount_value = self.discount_value
        if not discount_value:
            return currency(0)
        subtotal = self.get_purchase_subtotal()
        assert subtotal > 0, ('the subtotal should not be zero '
                              'at this point')
        total = subtotal - discount_value
        percentage = (1 - total / subtotal) * 100
        return percentage

    discount_percentage = property(_get_discount_by_percentage,
                                   _set_discount_by_percentage)

    def _set_surcharge_by_percentage(self, value):
        """Sets a surcharge by percentage.
        Note that surcharge must be added as an absolute value not as a
        factor like 0.97 = 3 % of discount.
        The correct form is 'percentage = 3' for a surcharge of 3 %"""
        self.surcharge_value = self._get_percentage_value(value)

    def _get_surcharge_by_percentage(self):
        surcharge_value = self.surcharge_value
        if not surcharge_value:
            return currency(0)
        subtotal = self.get_purchase_subtotal()
        assert subtotal > 0, ('the subtotal should not be zero '
                              'at this point')
        total = subtotal + surcharge_value
        percentage = ((total / subtotal) - 1) * 100
        return percentage

    surcharge_percentage = property(_get_surcharge_by_percentage,
                                 _set_surcharge_by_percentage)
    def reset_discount_and_surcharge(self):
        self.discount_value = self.surcharge_value = currency(0)

    def can_close(self):
        for item in self.get_items():
            if not item.has_been_received():
                return False
        return True

    def close(self):
        if not self.status == self.ORDER_CONFIRMED:
            raise ValueError('Invalid status, it should be confirmed'
                             'got %s instead' % self.get_status_str())
        self.status = self.ORDER_CLOSED

    def increase_quantity_received(self, sellable,
                                   quantity_received):
        items = [item for item in self.get_items()
                    if item.sellable.id == sellable.id]
        qty = len(items)
        if not qty:
            raise ValueError('There is no purchase item for '
                             'sellable %r' % sellable)
        if qty > 1:
            raise DatabaseInconsistency('It should have only one item for '
                                        'this sellable, got %d instead'
                                        % qty)
        item = items[0]
        item.quantity_received += quantity_received

    #
    # Classmethods
    #

    @classmethod
    def translate_status(cls, status):
        if not cls.statuses.has_key(status):
            raise DatabaseInconsistency('Got an unexpected status value: '
                                        '%s' % status)
        return cls.statuses[status]

    #
    # Accessors
    #

    def get_status_str(self):
        return PurchaseOrder.translate_status(self.status)

    def get_freight_type_name(self):
        if not self.freight_type in self.freight_types.keys():
            raise DatabaseInconsistency('Invalid freight_type, got %d'
                                        % self.freight_type)
        return self.freight_types[self.freight_type]

    def get_branch_name(self):
        return self.branch.get_description()

    def get_supplier_name(self):
        return self.supplier.get_description()

    def get_transporter_name(self):
        if not self.transporter:
            return u""
        return self.transporter.get_description()

    def get_order_number_str(self):
        return u'%05d' % self.order_number

    def get_purchase_subtotal(self):
        total = sum([i.get_total() for i in self.get_items()], currency(0))
        return currency(total)

    def get_purchase_total(self):
        subtotal = self.get_purchase_subtotal()
        total = subtotal - self.discount_value + self.surcharge_value
        if total < 0:
            raise ValueError('Purchase total can not be lesser than zero')
        return currency(total)

    def get_received_total(self):
        total = sum([item.cost * item.quantity_received
                        for item in self.get_items()], currency(0))
        return currency(total)

    def get_remaining_total(self):
        return self.get_purchase_total() - self.get_received_total()

    def get_pending_items(self):
        return [item for item in self.get_items()
                        if not item.has_been_received()]

    def get_received_items(self):
        return [item for item in self.get_items() if item.has_been_received()]


    def get_open_date_as_string(self):
        return self.open_date and self.open_date.strftime("%x") or ""

class PurchaseOrderAdaptToPaymentGroup(AbstractPaymentGroup):

    #
    # IPaymentGroup implementation
    #

#     def set_thirdparty(self, person):
#         """Define a new thirdparty. The parameter is a person, but also have
#         to implement specific facets to each PaymentGroup adapter. """
#         supplier = ISupplier(person)
#         if not supplier:
#             raise StoqlibError("the purchase thirdparty should have an "
#                                "ISupplier facet at this point")
#         order = self.get_adapted()
#         order.supplier = supplier

    def get_thirdparty(self):
        order = self.get_adapted()
        if not order.supplier:
            raise DatabaseInconsistency('An order must have a supplier')
        return order.supplier.person

    def get_group_description(self):
        order = self.get_adapted()
        return _(u'order %s') % order.order_number

    def create_preview_outpayments(self):
        conn = self.get_connection()
        base_method = sysparam(conn).BASE_PAYMENT_METHOD
        order = self.get_adapted()
        total = order.get_purchase_total()
        #first_due_date = order.expected_receival_date
        order._create_preview_outpayments(conn=conn, group=self,
                                          base_method=base_method,
                                          total=total)

PurchaseOrder.registerFacet(PurchaseOrderAdaptToPaymentGroup, IPaymentGroup)


#
# Views
#

class PurchaseOrderView(SQLObject, BaseSQLView):
    """General information about purchase orders"""
    status = IntCol()
    order_number = IntCol()
    open_date = DateTimeCol()
    quote_deadline = DateTimeCol()
    expected_receival_date = DateTimeCol()
    expected_pay_date = DateTimeCol()
    receival_date = DateTimeCol()
    confirm_date = DateTimeCol()
    salesperson_name = UnicodeCol()
    freight = DecimalCol()
    surcharge_value = PriceCol()
    discount_value = PriceCol()
    supplier_name = UnicodeCol()
    transporter_name = UnicodeCol()
    branch_name = UnicodeCol()
    ordered_quantity = DecimalCol()
    received_quantity = DecimalCol()
    subtotal = DecimalCol()
    total = DecimalCol()

    def get_transporter_name(self):
        return self.transporter_name or u""

    def get_open_date_as_string(self):
        return self.open_date.strftime("%x")

    def get_status_str(self):
        return PurchaseOrder.translate_status(self.status)
