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
##      Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Domain classes for renegotiation management """

from sqlobject import ForeignKey, UnicodeCol, IntCol
from zope.interface import implements
from kiwi.datatypes import currency

from stoqlib.database.columns import PriceCol
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.exceptions import StoqlibError
from stoqlib.domain.base import Domain, InheritableModelAdapter
from stoqlib.domain.interfaces import (IRenegotiationReturnSale,
                                       IDescribable, IPaymentGroup,
                                       IRenegotiationExchange,
                                       IRenegotiationInstallments)

_ = stoqlib_gettext


#
# Base Domain Classes
#

class RenegotiationData(Domain):
    """A base class for sale order renegotiations

    Note::

        if return_total > 0: the store must return money to customer
        if return_total < 0: the customer must pay to store this value
        if return_total = 0: there is no financial transaction tied with
                             this return operation
    """

    reason = UnicodeCol(default=None)
    paid_total = PriceCol()
    invoice_number = IntCol()
    penalty_value = PriceCol(default=0)
    responsible = ForeignKey('Person')
    new_order = ForeignKey("Sale", default=None)

    #
    # Accessors
    #

    def get_return_total(self):
        total = self.paid_total - self.penalty_value
        return currency(total)

    def get_new_order_number(self):
        if not self.new_order:
            return u""
        return self.new_order.get_order_number_str()


#
# Adapters
#

class AbstractRenegotiationAdapter(InheritableModelAdapter):
    implements(IDescribable)

    type_description = None

    def get_description(self):
        return self.type_description

#     def get_return_value_description(self):
#         adapted = self.get_adapted()
#         if not adapted.get_return_total():
#             return u""
#         if adapted.new_order is None:
#             return _(u"Paid by Money")
#         return _(u"Paid on sale order %s"
#                  % adapted.new_order.get_order_number_str())


class RenegotiationAdaptToReturnSale(AbstractRenegotiationAdapter):
    implements(IRenegotiationReturnSale, IDescribable)

    type_description = _(u"Return Sale")

    _inheritable = False

    def _setup_giftcert_renegotiation(self, sale_order, giftcert_number,
                                      overpaid_value, reason):
        clone = sale_order.get_clone()
        conn = self.get_connection()

        if not giftcert_number:
            raise StoqlibError("You should provide a valid gift "
                               "certificate number at this point")
        clone.add_custom_gift_certificate(overpaid_value,
                                          giftcert_number)

        from stoqlib.domain.payment.methods import GiftCertificatePM
        group = clone.addFacet(IPaymentGroup, connection=conn)
        method = GiftCertificatePM.selectOne(connection=conn)
        method.create_inpayment(overpaid_value, group)
        clone.confirm_sale()

        # The new payment for the new sale has it's value already paid
        # in the old sale order. So, create a reversal one
        payment = IPaymentGroup(sale_order)
        payment.add_payment(-overpaid_value, reason, method)
        return clone

    def confirm(self, sale_order, gift_certificate_settings=None):
        """Confirm the return operation """
        from stoqlib.domain.sale import GiftCertificateOverpaidSettings
        adapted = self.get_adapted()
        if not adapted.get_return_total():
            # There is no return value and also nothing special to be done
            sale_order.cancel(self)
            return

        if not gift_certificate_settings:
            raise StoqlibError("You must specify informations about how "
                               "to deal with the return value")

        regtype = gift_certificate_settings.renegotiation_type
        overpaid_value = gift_certificate_settings.renegotiation_value
        group = sale_order.check_payment_group()
        reason = (u'1/1 Money returned for renegotiation of sale %s'
                  % sale_order.get_order_number_str())

        if regtype == GiftCertificateOverpaidSettings.TYPE_RETURN_MONEY:
            group.create_debit(-overpaid_value, reason, sale_order.till)

        elif (regtype ==
              GiftCertificateOverpaidSettings.TYPE_GIFT_CERTIFICATE):
            number = gift_certificate_settings.gift_certificate_number
            clone = self._setup_giftcert_renegotiation(sale_order, number,
                                                       overpaid_value, reason)
            adapted.new_order = clone

        else:
            raise StoqlibError("Invalid renegotiation type, got %s"
                               % regtype)
        sale_order.cancel(self)

RenegotiationData.registerFacet(RenegotiationAdaptToReturnSale,
                                IRenegotiationReturnSale)


class RenegotiationAdaptToExchange(AbstractRenegotiationAdapter):
    implements(IRenegotiationExchange, IDescribable)

    type_description = _("Exchange")

    _inheritable = False

    def confirm(self):
        # TODO to be implemented on bug 2230
        pass

RenegotiationData.registerFacet(RenegotiationAdaptToExchange,
                                IRenegotiationExchange)


class RenegotiationAdaptToChangeInstallments(AbstractRenegotiationAdapter):
    implements(IRenegotiationInstallments, IDescribable)

    type_description = _("Installments Renegotiation")

    _inheritable = False

    def confirm(self):
        # TODO to be implemented on bug 2190
        pass

RenegotiationData.registerFacet(RenegotiationAdaptToChangeInstallments,
                                IRenegotiationInstallments)
