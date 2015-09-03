# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2014 Async Open Source <http://www.async.com.br>
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
""" Stock Decrease object and related objects implementation """

# pylint: enable=E1101

from decimal import Decimal

from kiwi.currency import currency
from storm.references import Reference
from zope.interface import implementer

from stoqlib.database.properties import (UnicodeCol, DateTimeCol, IntCol,
                                         PriceCol, QuantityCol, IdentifierCol,
                                         IdCol, EnumCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.fiscal import Invoice
from stoqlib.domain.interfaces import IContainer, IInvoice, IInvoiceItem
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.product import ProductHistory, StockTransactionHistory
from stoqlib.domain.taxes import check_tax_info_presence
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext

#
# Base Domain Classes
#


@implementer(IInvoiceItem)
class StockDecreaseItem(Domain):
    """An item in a stock decrease object.

    Note that objects of this type should not be created manually, only by
    calling :meth:`StockDecrease.add_sellable`
    """

    __storm_table__ = 'stock_decrease_item'

    stock_decrease_id = IdCol(default=None)

    #: The stock decrease this item belongs to
    stock_decrease = Reference(stock_decrease_id, 'StockDecrease.id')

    sellable_id = IdCol()

    #: the |sellable| for this decrease
    sellable = Reference(sellable_id, 'Sellable.id')

    batch_id = IdCol()

    #: If the sellable is a storable, the |batch| that it was removed from
    batch = Reference(batch_id, 'StorableBatch.id')

    #: the cost of the |sellable| on the moment this decrease was created
    cost = PriceCol(default=0)

    #: the quantity decreased for this item
    quantity = QuantityCol()

    #: Id of ICMS tax in product tax template
    icms_info_id = IdCol()

    #:the :class:`stoqlib.domain.taxes.InvoiceItemIcms` tax for *self*
    icms_info = Reference(icms_info_id, 'InvoiceItemIcms.id')

    #: Id of IPI tax in product tax template
    ipi_info_id = IdCol()

    #: the :class:`stoqlib.domain.taxes.InvoiceItemIpi` tax for *self*
    ipi_info = Reference(ipi_info_id, 'InvoiceItemIpi.id')

    #: Id of PIS tax in product tax template
    pis_info_id = IdCol()

    #: the :class:`stoqlib.domain.taxes.InvoiceItemPis` tax for *self*
    pis_info = Reference(pis_info_id, 'InvoiceItemPis.id')

    #: Id of COFINS tax in product tax template
    cofins_info_id = IdCol()

    #: the :class:`stoqlib.domain.taxes.InvoiceItemCofins` tax for *self*
    cofins_info = Reference(cofins_info_id, 'InvoiceItemCofins.id')

    item_discount = Decimal('0')

    def __init__(self, store=None, sellable=None, **kwargs):
        if sellable is None:
            raise TypeError('You must provide a sellable argument')
        check_tax_info_presence(kwargs, store)

        super(StockDecreaseItem, self).__init__(store=store, sellable=sellable,
                                                **kwargs)

        product = self.sellable.product
        if product:
            self.ipi_info.set_item_tax(self)
            self.icms_info.set_item_tax(self)
            self.pis_info.set_item_tax(self)
            self.cofins_info.set_item_tax(self)

    #
    # Properties
    #

    @property
    def total_cost(self):
        return currency(self.cost * self.quantity)

    #
    # IInvoiceItem implementation
    #

    @property
    def parent(self):
        return self.stock_decrease

    @property
    def base_price(self):
        return self.cost

    @property
    def price(self):
        return self.cost

    @property
    def nfe_cfop_code(self):
        cfop = self.stock_decrease.cfop.code
        return cfop.replace('.', '')

    #
    # Public API
    #

    def decrease(self, branch):
        # FIXME: We should not be receiving a branch here. We should be using
        # self.stock_decrease.branch for that.
        assert branch

        storable = self.sellable.product_storable
        if storable:
            storable.decrease_stock(self.quantity, branch,
                                    StockTransactionHistory.TYPE_STOCK_DECREASE,
                                    self.id,
                                    cost_center=self.stock_decrease.cost_center,
                                    batch=self.batch)

    #
    # Accessors
    #

    def get_total(self):
        return currency(self.cost * self.quantity)

    def get_quantity_unit_string(self):
        unit = self.sellable.unit_description
        if unit:
            return u"%s %s" % (self.quantity, unit)
        return unicode(self.quantity)

    def get_description(self):
        return self.sellable.get_description()


@implementer(IContainer)
@implementer(IInvoice)
class StockDecrease(Domain):
    """Stock Decrease object implementation.

    Stock Decrease is when the user need to manually decrease the stock
    quantity, for some reason that is not a sale, transfer or other cases
    already covered in stoqlib.
    """

    __storm_table__ = 'stock_decrease'

    #: Stock Decrease is still being edited
    STATUS_INITIAL = u'initial'

    #: Stock Decrease is confirmed and stock items have been decreased.
    STATUS_CONFIRMED = u'confirmed'

    statuses = {STATUS_INITIAL: _(u'Opened'),
                STATUS_CONFIRMED: _(u'Confirmed')}

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: status of the sale
    status = EnumCol(allow_none=False, default=STATUS_INITIAL)

    reason = UnicodeCol(default=u'')

    #: Some optional additional information related to this sale.
    notes = UnicodeCol(default=u'')

    #: the date sale was created
    confirm_date = DateTimeCol(default_factory=localnow)

    responsible_id = IdCol()

    #: who should be blamed for this
    responsible = Reference(responsible_id, 'LoginUser.id')

    removed_by_id = IdCol()

    removed_by = Reference(removed_by_id, 'Employee.id')

    branch_id = IdCol()

    #: branch where the sale was done
    branch = Reference(branch_id, 'Branch.id')

    #: person who is receiving
    person_id = IdCol()

    person = Reference(person_id, 'Person.id')

    #: the choosen CFOP
    cfop_id = IdCol()

    cfop = Reference(cfop_id, 'CfopData.id')

    # FIXME: Duplicated from Invoice. Remove it
    #: The invoice number of the stock decrease
    invoice_number = IntCol()

    #: the payment group related to this stock decrease
    group_id = IdCol()

    group = Reference(group_id, 'PaymentGroup.id')

    cost_center_id = IdCol()

    #: the |costcenter| that the cost of the products decreased in this stock
    #: decrease should be accounted for. When confirming a stock decrease with
    #: a |costcenter| set, a |costcenterentry| will be created for each product
    #: decreased.
    cost_center = Reference(cost_center_id, 'CostCenter.id')

    #: |transporter| used in stock decrease
    transporter = None

    invoice_id = IdCol()

    #: The |invoice| generated by the stock decrease
    invoice = Reference(invoice_id, 'Invoice.id')

    def __init__(self, store=None, **kwargs):
        kwargs['invoice'] = Invoice(store=store, invoice_type=Invoice.TYPE_OUT)
        super(StockDecrease, self).__init__(store=store, **kwargs)

    #
    # IInvoice implementation
    #

    @property
    def comments(self):
        return self.reason

    @property
    def discount_value(self):
        return currency(0)

    @property
    def invoice_subtotal(self):
        return currency(self.get_total_cost())

    @property
    def invoice_total(self):
        return currency(self.get_total_cost())

    @property
    def payments(self):
        if self.group:
            return self.group.get_valid_payments().order_by(Payment.open_date)
        return None

    @property
    def recipient(self):
        return self.person

    @property
    def operation_nature(self):
        # TODO: Save the operation nature in new loan table field.
        return _(u"Stock decrease")

    #
    # Classmethods
    #

    @classmethod
    def get_status_name(cls, status):
        if not status in cls.statuses:
            raise DatabaseInconsistency(_(u"Invalid status %d") % status)
        return cls.statuses[status]

    def add_item(self, item):
        assert not item.stock_decrease
        item.stock_decrease = self

    def get_items(self):
        return self.store.find(StockDecreaseItem, stock_decrease=self)

    def remove_item(self, item):
        item.stock_decrease = None
        self.store.maybe_remove(item)

    # Status

    def can_confirm(self):
        """Only stock decreases with status equal to INITIAL can be confirmed

        :returns: ``True`` if the stock decrease can be confirmed, otherwise ``False``
        """
        return self.status == StockDecrease.STATUS_INITIAL

    def confirm(self):
        """Confirms the stock decrease

        """
        assert self.can_confirm()
        assert self.branch

        store = self.store
        branch = self.branch
        for item in self.get_items():
            if item.sellable.product:
                ProductHistory.add_decreased_item(store, branch, item)
            item.decrease(branch)

        self.status = StockDecrease.STATUS_CONFIRMED

        # Save the invoice number, operation_nature and branch in Invoice Table
        self.invoice.invoice_number = self.invoice_number
        self.invoice.operation_nature = self.operation_nature
        self.invoice.branch = branch

        if self.group:
            self.group.confirm()

    #
    # Accessors
    #

    def get_branch_name(self):
        return self.branch.get_description()

    def get_responsible_name(self):
        return self.responsible.get_description()

    def get_removed_by_name(self):
        if not self.removed_by:
            return u''

        return self.removed_by.get_description()

    def get_total_items_removed(self):
        return sum([item.quantity for item in self.get_items()], 0)

    def get_cfop_description(self):
        return self.cfop.get_description()

    def get_total_cost(self):
        return self.get_items().sum(StockDecreaseItem.cost *
                                    StockDecreaseItem.quantity)

    # Other methods

    def add_sellable(self, sellable, cost=None, quantity=1, batch=None):
        """Adds a new sellable item to a stock decrease

        :param sellable: the |sellable|
        :param cost: the cost for the decrease. If ``None``, sellable.cost
            will be used instead
        :param quantity: quantity to add, defaults to ``1``
        :param batch: the |batch| this sellable comes from, if the sellable is a
          storable. Should be ``None`` if it is not a storable or if the storable
          does not have batches.
        """
        self.validate_batch(batch, sellable=sellable)
        if cost is None:
            cost = sellable.cost

        return StockDecreaseItem(store=self.store,
                                 quantity=quantity,
                                 stock_decrease=self,
                                 sellable=sellable,
                                 batch=batch,
                                 cost=cost)
