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

import datetime
import decimal
from zope.interface import implements

from kiwi.currency import currency

from stoqlib.database.orm import AutoReload
from stoqlib.database.orm import (ForeignKey, UnicodeCol, DateTimeCol, IntCol,
                                  PriceCol, QuantityCol, MultipleJoin)
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.base import Domain
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.interfaces import IContainer
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ReturnedSaleItem(Domain):
    """An item of a :class:`returned sale <ReturnedSale>`"""

    #: the returned quantity
    quantity = QuantityCol(default=0)

    #: The price which this :obj:`.sale_item` was sold.
    #: When creating this object, if *price* is not passed to the
    #: contructor, it defaults to :obj:`.sale_item.price` or
    #: :obj:`.sellable.price`
    price = PriceCol()

    #: the returned |saleitem|
    sale_item = ForeignKey('SaleItem', default=None)

    #: The returned |sellable|
    #: Note that if :obj:`.sale_item` != ``None``, this is the same as
    #: :obj:`.sale_item.sellable`
    sellable = ForeignKey('Sellable')

    #: the |returnedsale| which this item belongs
    returned_sale = ForeignKey('ReturnedSale')

    @property
    def total(self):
        """The total being returned

        This is the same as :obj:`.price` * :obj:`.quantity`
        """
        return self.price * self.quantity

    #
    #  Domain
    #

    def _create(self, id, **kwargs):
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

        super(ReturnedSaleItem, self)._create(id, **kwargs)

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
            storable.increase_stock(self.quantity, branch)


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

    implements(IContainer)

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IntCol(default=AutoReload)

    #: the date this return was done
    return_date = DateTimeCol(default_factory=datetime.datetime.now)

    #: the invoice number for this returning
    invoice_number = IntCol(default=None)

    #: the reason why this return was made
    reason = UnicodeCol(default='')

    #: the |sale| we're returning
    sale = ForeignKey('Sale', default=None)

    #: if not ``None``, :obj:`.sale` was traded for this |sale|
    new_sale = ForeignKey('Sale', default=None)

    #: the |loginuser| responsible for doing this return
    responsible = ForeignKey('LoginUser')

    #: the |branch| in which this return happened
    branch = ForeignKey('Branch')

    #: a list of all items returned in this return
    returned_items = MultipleJoin('ReturnedSaleItem',
                                  joinColumn='returned_sale_id')

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

        returned = ReturnedSale.selectBy(connection=self.get_connection(),
                                         sale=self.sale)
        # This will sum the total already returned for this sale,
        # excluiding *self* that is in the same transaction
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
        ReturnedSaleItem.delete(item.id, connection=self.get_connection())

    #
    #  Public API
    #

    def return_(self):
        """Do the return of this returned sale.

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
            conn = self.get_connection()
            group = self.group
            for payment in [p for p in
                            group.get_pending_payments() if p.is_inpayment()]:
                # We are returning money to client, that means he doesn't owe
                # us anything, we do now. Cancel pending payments
                payment.cancel()
            method = PaymentMethod.get_by_name(conn, 'money')
            description = _('Money returned for sale %s') % (
                            self.sale.get_order_number_str(), )
            value = self.total_amount_abs
            payment = method.create_outpayment(group, self.branch, value,
                                               description=description)
            payment.set_pending()

        self._return_sale(payment)

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

        conn = self.get_connection()
        group = self.group
        method = PaymentMethod.get_by_name(conn, 'trade')
        description = _('Traded items for sale %s') % (
                        self.new_sale.get_order_number_str(), )
        value = self.returned_total
        payment = method.create_inpayment(group, self.branch, value,
                                          description=description)
        payment.set_pending()
        payment.pay()

        self._return_sale(payment)

    #
    #  Private
    #

    def _get_returned_percentage(self):
        return decimal.Decimal(self.returned_total / self.sale.total_amount)

    def _clean_not_used_items(self):
        conn = self.get_connection()
        for item in self.returned_items:
            if not item.quantity:
                # Removed items not marked for return
                item.delete(item.id, connection=conn)

    def _return_sale(self, payment):
        # We must have at least one item to return
        assert self.returned_items.count()

        branch = get_current_branch(self.get_connection())
        for item in self.returned_items:
            item.return_(branch)

        if self.sale:
            # FIXME: For now, we are not reverting the comission as there is a
            # lot of things to consider. See bug 5215 for information about it.
            #self._revert_commission(payment)
            self._revert_fiscal_entry()
            self.sale.return_(self)

    def _revert_fiscal_entry(self):
        entry = FiscalBookEntry.selectOneBy(connection=self.get_connection(),
                                            payment_group=self.group,
                                            is_reversal=False)
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

    def _revert_commission(self, payment):
        from stoqlib.domain.commission import Commission
        conn = self.get_connection()
        old_commissions = Commission.selectBy(connection=conn,
                                              sale=self.sale)
        old_commissions_total = old_commissions.sum(Commission.value)
        if old_commissions_total <= 0:
            # Comission total should not be negative
            return

        # old_commissions_paid, unlike old_commissions_total, contains the
        # total positive generated commission, so we can revert it partially
        old_commissions_paid = old_commissions.filter(
            Commission.value >= 0).sum(Commission.value)
        value = old_commissions_paid * self._get_returned_percentage()
        assert old_commissions_total - value >= 0

        Commission(
            connection=conn,
            commission_type=old_commissions[0].commission_type,
            sale=self.sale,
            payment=payment,
            salesperson=self.sale.salesperson,
            # Generate a negative commission to compensate the returned items
            value=-value,
            )
