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

from kiwi.currency import currency

from stoqlib.database.orm import (ForeignKey, UnicodeCol, DateTimeCol, IntCol,
                                  PriceCol, QuantityCol, MultipleJoin)
from stoqlib.domain.base import Domain
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ReturnedSaleItem(Domain):
    """An item of a :class:`returned sale <ReturnedSale>`"""

    #: the returned quantity
    quantity = QuantityCol(default=0)

    #: the returned :class:`sale item <stoqlib.domain.saleSaleItem>`
    sale_item = ForeignKey('SaleItem')

    #: the :class:`returned sale <ReturnedSale>` which this item belongs
    returned_sale = ForeignKey('ReturnedSale')

    @property
    def sellable(self):
        """The returned :class:`sellable <stoqlib.domain.sellable.Sellable>`

        Note that this is the same as :obj:`.sale_item.sellable`
        """
        return self.sale_item.sellable

    @property
    def sale_price(self):
        """The price which this :obj:`.sale_item` was sold

        Note that this is the same as :obj:`.sale_item.price`
        """
        return self.sale_item.price

    @property
    def total(self):
        """The total being returned

        This is the same as :obj:`.sale_price` * :obj:`.quantity`
        """
        return self.sale_price * self.quantity

    #
    #  Public API
    #

    def return_(self, branch):
        """See :meth:`stoqlib.domain.sale.SaleItem.return_`"""
        return self.sale_item.return_(branch, self)


class ReturnedSale(Domain):
    """Holds information about returned
    :class:`sales <stoqlib.domain.sale.Sale>`
    """

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IntCol()

    #: the date this return was done
    return_date = DateTimeCol(default=datetime.datetime.now)

    #: the invoice number for this returning
    invoice_number = IntCol(default=None)

    #: a discount to apply on this return
    discount_value = PriceCol(default=0)

    #: a penalty to apply on this return
    penalty_value = PriceCol(default=0)

    #: the reason why this return was made
    reason = UnicodeCol(default='')

    #: the actual returned :class:`sale <stoqlib.domain.sale.Sale>`
    sale = ForeignKey('Sale')

    #: the :class:`user <stoqlib.domain.person.LoginUser>` responsible
    #: for doing this return
    responsible = ForeignKey('LoginUser')

    #: the :class:`branch <stoqlib.domain.person.Branch>` in which
    #: this return happened
    branch = ForeignKey('Branch')

    #: a list of all items returned in this return
    returned_items = MultipleJoin('ReturnedSaleItem',
                                  joinColumn='returned_sale_id')

    @property
    def group(self):
        """The :class:`group <stoqlib.domain.payment.group.PaymentGroup>` of
        this return

        Note that this is the same as :obj:`.sale.group`
        """
        return self.sale.group

    @property
    def client(self):
        """The :class:`client <stoqlib.domain.personClient>` of this return

        Note that this is the same as :obj:`.sale.client`
        """
        return self.sale.client

    @property
    def sale_total(self):
        """The current total amount of the sale

        This is calculated by getting the
        :attr:`total amount <stoqlib.domain.sale.Sale.total_amount>` of the
        returned sale and subtracting the sum of :obj:`.returned_total` of
        all existing returns for the same sale.
        """
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
        return self._get_subtotal(with_additions=True)

    @property
    def total_amount_abs(self):
        """The absolute total amount for this return

        This is the same as abs(:attr:`.total_amount`). Useful for
        displaying it on a gui, just changing it's label to show if
        it's 'overpaid' or 'missing'.
        """
        return currency(abs(self.total_amount))

    #
    #  Public API
    #

    def return_(self):
        """Do the real return of this return

        If :attr:`.total_amount` is > 0, the client is returning more
        than he paid, we will create an
        :`out payment <stoqlib.domain.payment.payment.Payment>` with that
        value so the client can be reversed. If it's 0, than he is
        returning the same amount he still needed to pay, so existing
        payments will be cancelled and the client doesn't own anything
        to us. If it's < 0, than the payments need to be reajusted
        before calling this.

        See :meth:`stoqlib.domain.sale.Sale.return_` too as that will
        be called after that payment logic is done.
        """
        conn = self.get_connection()
        for item in self.returned_items:
            if not item.quantity:
                # Removed items not marked for return
                item.delete(item.id, connection=conn)

        # We must have at least one item to return
        assert self.returned_items.count()

        payment = None
        if self.total_amount == 0:
            # The client does not owe anything to us
            self.group.cancel()
        elif self.total_amount < 0:
            # The user has paid more than it's returning
            group = self.group
            for payment in [p for p in
                            group.get_pending_payments() if p.is_inpayment()]:
                # We are returning money to client, that means he doesn't owe
                # us anything, we do now. Cancel existing pending inpayments
                payment.cancel()
            method = PaymentMethod.get_by_name(conn, 'money')
            description = _('Money returned for sale %s') % (
                            self.sale.get_order_number_str(), )
            value = currency(abs(self._get_subtotal()))
            payment = method.create_outpayment(group, self.branch, value,
                                               description=description)
            payment.discount = self.penalty_value
            payment.penalty = self.discount_value
            payment.set_pending()

        self._revert_fiscal_entry()
        # FIXME: For now, we are not reverting the comission as there is a lot
        # of things to consider. See bug 5215 for information about it.
        #self._revert_commission(payment)

        self.sale.return_(self)

    #
    #  Private
    #

    def _get_subtotal(self, with_additions=False):
        subtotal = self.sale_total - self.paid_total - self.returned_total
        if with_additions:
            # This is used above on return_ to create a payment with the
            # subtotal and than put penalty/discount where they belong
            # instead of having them already summed on value
            subtotal -= self.discount_value
            subtotal += self.penalty_value

        return currency(subtotal)

    def _get_returned_percentage(self):
        return decimal.Decimal(self.returned_total / self.sale.total_amount)

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
