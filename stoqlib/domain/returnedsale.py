# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

# pylint: enable=E1101

import decimal

from kiwi.currency import currency
from storm.references import Reference, ReferenceSet
from zope.interface import implementer

from stoqlib.database.properties import (UnicodeCol, DateTimeCol, IntCol,
                                         PriceCol, QuantityCol, IdentifierCol,
                                         IdCol)
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.base import Domain
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.interfaces import IContainer
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ReturnedSaleItem(Domain):
    """An item of a :class:`returned sale <ReturnedSale>`

    Note that objects of this type should never be created manually, only by
    calling :meth:`Sale.create_sale_return_adapter`
    """

    __storm_table__ = 'returned_sale_item'

    #: the returned quantity
    quantity = QuantityCol(default=0)

    #: The price which this :obj:`.sale_item` was sold.
    #: When creating this object, if *price* is not passed to the
    #: contructor, it defaults to :obj:`.sale_item.price` or
    #: :obj:`.sellable.price`
    price = PriceCol()

    sale_item_id = IdCol(default=None)

    #: the returned |saleitem|
    sale_item = Reference(sale_item_id, 'SaleItem.id')

    sellable_id = IdCol()

    #: The returned |sellable|
    #: Note that if :obj:`.sale_item` != ``None``, this is the same as
    #: :obj:`.sale_item.sellable`
    sellable = Reference(sellable_id, 'Sellable.id')

    batch_id = IdCol()

    #: If the sellable is a storable, the |batch| that it was removed from
    batch = Reference(batch_id, 'StorableBatch.id')

    returned_sale_id = IdCol()

    #: the |returnedsale| which this item belongs
    returned_sale = Reference(returned_sale_id, 'ReturnedSale.id')

    def __init__(self, store=None, **kwargs):
        # TODO: Add batch logic here. (get if from sale_item or check if was
        # passed togheter with sellable)
        sale_item = kwargs.get('sale_item')
        sellable = kwargs.get('sellable')

        if not sale_item and not sellable:
            raise ValueError(
                "A sale_item or a sellable is mandatory to create this object")
        elif sale_item and sellable and sale_item.sellable != sellable:
            raise ValueError(
                "sellable must be the same as sale_item.sellable")
        elif sale_item and not sellable:
            sellable = sale_item.sellable
            kwargs['sellable'] = sellable

        if not 'price' in kwargs:
            # sale_item.price takes priority over sellable.price
            kwargs['price'] = sale_item.price if sale_item else sellable.price

        super(ReturnedSaleItem, self).__init__(store=store, **kwargs)

    @property
    def total(self):
        """The total being returned

        This is the same as :obj:`.price` * :obj:`.quantity`
        """
        return self.price * self.quantity

    #
    #  Public API
    #

    def return_(self, branch):
        """Do the real return of this item

        When calling this, the real return will happen, that is,
        if :obj:`.sellable` is a |product|, it's stock will be
        increased on *branch*.
        """
        storable = self.sellable.product_storable
        if storable:
            storable.increase_stock(self.quantity, branch,
                                    StockTransactionHistory.TYPE_RETURNED_SALE,
                                    self.id, batch=self.batch)
        if self.sale_item:
            self.sale_item.quantity_decreased -= self.quantity


@implementer(IContainer)
class ReturnedSale(Domain):
    """Holds information about a returned |sale|.

    This can be:
      * *trade*, a |client| is returning the |sale| and buying something
        new with that credit. In that case the returning sale is :obj:`.sale` and the
        replacement |sale| is in :obj:`.new_sale`.
      * *return sale* or *devolution*, a |client| is returning the |sale|
        without making a new |sale|.

    Normally the old sale which is returned is :obj:`.sale`, however it
    might be ``None`` in some situations for example, if the |sale| was done
    at a different |branch| that hasn't been synchronized or is using another
    system.
    """

    __storm_table__ = 'returned_sale'

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: the date this return was done
    return_date = DateTimeCol(default_factory=localnow)

    #: the invoice number for this returning
    invoice_number = IntCol(default=None)

    #: the reason why this return was made
    reason = UnicodeCol(default=u'')

    sale_id = IdCol(default=None)

    #: the |sale| we're returning
    sale = Reference(sale_id, 'Sale.id')

    new_sale_id = IdCol(default=None)

    #: if not ``None``, :obj:`.sale` was traded for this |sale|
    new_sale = Reference(new_sale_id, 'Sale.id')

    responsible_id = IdCol()

    #: the |loginuser| responsible for doing this return
    responsible = Reference(responsible_id, 'LoginUser.id')

    branch_id = IdCol()

    #: the |branch| in which this return happened
    branch = Reference(branch_id, 'Branch.id')

    #: a list of all items returned in this return
    returned_items = ReferenceSet('id', 'ReturnedSaleItem.returned_sale_id')

    @property
    def group(self):
        """|paymentgroup| for this return sale.

        Can return:
          * For a *trade*, use the |paymentgroup| from
            the replacement |sale|.
          * For a *devolution*, use the |paymentgroup| from
            the returned |sale|.
        """
        if self.new_sale:
            return self.new_sale.group
        if self.sale:
            return self.sale.group
        return None

    @property
    def client(self):
        """The |client| of this return

        Note that this is the same as :obj:`.sale.client`
        """
        return self.sale and self.sale.client

    @property
    def sale_total(self):
        """The current total amount of the |sale|.

        This is calculated by getting the
        :attr:`total amount <stoqlib.domain.sale.Sale.total_amount>` of the
        returned sale and subtracting the sum of :obj:`.returned_total` of
        all existing returns for the same sale.
        """
        if not self.sale:
            return currency(0)

        returned = self.store.find(ReturnedSale,
                                   sale=self.sale)
        # This will sum the total already returned for this sale,
        # excluiding *self* within the same store
        returned_total = sum([returned_sale.returned_total for returned_sale in
                              returned if returned_sale != self])

        return currency(self.sale.total_amount - returned_total)

    @property
    def paid_total(self):
        """The total paid for this sale

        Note that this is the same as
        :meth:`stoqlib.domain.sale.Sale.get_total_paid`
        """
        if not self.sale:
            return currency(0)

        return self.sale.get_total_paid()

    @property
    def returned_total(self):
        """The total being returned on this return

        This is done by summing the :attr:`ReturnedSaleItem.total` of
        all of this :obj:`returned items <.returned_items>`
        """
        return currency(sum([item.total for item in self.returned_items]))

    @property
    def total_amount(self):
        """The total amount for this return

        See :meth:`.return_` for details of how this is used.
        """
        return currency(self.sale_total -
                        self.paid_total -
                        self.returned_total)

    @property
    def total_amount_abs(self):
        """The absolute total amount for this return

        This is the same as abs(:attr:`.total_amount`). Useful for
        displaying it on a gui, just changing it's label to show if
        it's 'overpaid' or 'missing'.
        """
        return currency(abs(self.total_amount))

    #
    #  IContainer implementation
    #

    def add_item(self, returned_item):
        assert not returned_item.returned_sale
        returned_item.returned_sale = self

    def get_items(self):
        return self.returned_items

    def remove_item(self, item):
        item.returned_sale = None
        self.store.maybe_remove(item)

    #
    #  Public API
    #

    def return_(self, method_name=u'money'):
        """Do the return of this returned sale.

        :param unicode method_name: The name of the payment method that will be
          used to create this payment.

        If :attr:`.total_amount` is:
          * > 0, the client is returning more than it paid, we will create
            a |payment| with that value so the |client| can be reversed.
          * == 0, the |client| is returning the same amount that needs to be paid,
            so existing payments will be cancelled and the |client| doesn't
            owe anything to us.
          * < 0, than the payments need to be readjusted before calling this.

        .. seealso: :meth:`stoqlib.domain.sale.Sale.return_` as that will be
           called after that payment logic is done.
        """
        assert self.sale and self.sale.can_return()
        self._clean_not_used_items()

        payment = None
        if self.total_amount == 0:
            # The client does not owe anything to us
            self.group.cancel()
        elif self.total_amount < 0:
            # The user has paid more than it's returning
            for payment in self.group.get_pending_payments():
                if payment.is_inpayment():
                    # We are returning money to client, that means he doesn't owe
                    # us anything, we do now. Cancel pending payments
                    payment.cancel()

            method = PaymentMethod.get_by_name(self.store, method_name)
            description = _(u'%s returned for sale %s') % (method.description,
                                                           self.sale.identifier)
            payment = method.create_payment(Payment.TYPE_OUT,
                                            payment_group=self.group,
                                            branch=self.branch,
                                            value=self.total_amount_abs,
                                            description=description)
            payment.set_pending()
            if method_name == u'credit':
                payment.pay()

        self._return_items()
        # FIXME: For now, we are not reverting the comission as there is a
        # lot of things to consider. See bug 5215 for information about it.
        self._revert_fiscal_entry()
        self.sale.return_(self)

    def trade(self):
        """Do a trade for this return

        Almost the same as :meth:`.return_`, but unlike it, this won't
        generate reversed payments to the client. Instead, it'll
        generate an inpayment using :obj:`.returned_total` value,
        so it can be used as an "already paid quantity" on :obj:`.new_sale`.
        """
        assert self.new_sale
        if self.sale:
            assert self.sale.can_return()
        self._clean_not_used_items()

        store = self.store
        group = self.group
        method = PaymentMethod.get_by_name(store, u'trade')
        description = _(u'Traded items for sale %s') % (
            self.new_sale.identifier, )
        value = self.returned_total

        self._return_items()

        value_as_discount = sysparam.get_bool('USE_TRADE_AS_DISCOUNT')
        if value_as_discount:
            self.new_sale.discount_value = self.returned_total
        else:
            payment = method.create_payment(Payment.TYPE_IN, group, self.branch, value,
                                            description=description)
            payment.set_pending()
            payment.pay()
            self._revert_fiscal_entry()

        if self.sale:
            self.sale.return_(self)

    def remove(self):
        """Remove this return and it's items from the database"""
        # XXX: Why do we remove this object from the database
        for item in self.get_items():
            self.remove_item(item)
        self.store.remove(self)

    #
    #  Private
    #

    def _return_items(self):
        # We must have at least one item to return
        assert self.returned_items.count()

        branch = get_current_branch(self.store)
        for item in self.returned_items:
            item.return_(branch)

    def _get_returned_percentage(self):
        return decimal.Decimal(self.returned_total / self.sale.total_amount)

    def _clean_not_used_items(self):
        store = self.store
        for item in self.returned_items:
            if not item.quantity:
                # Removed items not marked for return
                item.delete(item.id, store=store)

    def _revert_fiscal_entry(self):
        entry = self.store.find(FiscalBookEntry,
                                payment_group=self.group,
                                is_reversal=False).one()
        if not entry:
            return

        # FIXME: Instead of doing a partial reversion of fiscal entries,
        # we should be reverting the exact tax for each returned item.
        returned_percentage = self._get_returned_percentage()
        entry.reverse_entry(
            self.invoice_number,
            icms_value=entry.icms_value * returned_percentage,
            iss_value=entry.iss_value * returned_percentage,
            ipi_value=entry.ipi_value * returned_percentage)
