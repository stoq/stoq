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
"""This module contains all related classes to the credit card payment method.
This includes:

- |creditprovider| - The institution that provided the credit for the client.
  Visanet and American Express, for instance
- |carddevice| - The device used to receive the |payment|.
- |cardcost| - Configuration for each |carddevice|
- |creditcarddata| - For each card |payment| created, one of this will also
  be saved with the card related information
"""

# pylint: enable=E1101

import collections

from zope.interface import implementer
from storm.expr import And, Delete, Or, Update
from storm.references import Reference

from stoqlib.database.properties import (PercentCol, PriceCol, DateTimeCol,
                                         IntCol, UnicodeCol, IdCol, EnumCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


@implementer(IDescribable)
class CreditProvider(Domain):
    """A credit provider

    This is the institution that provides the credit to the client, for
    instance: American Express, Visanet, Redecard, etc...
     """
    __storm_table__ = 'credit_provider'

    #: A short description of this provider
    short_name = UnicodeCol()

    #: An identification for this provider
    provider_id = UnicodeCol(default=u'')

    #: the maximum number of installments for a |sale| using this credit provider.
    max_installments = IntCol(default=1)

    default_device_id = IdCol()
    #: The default device for this credit provider. This will be suggested to
    #: the user when he selects this provider in the checkout dialog
    default_device = Reference(default_device_id, 'CardPaymentDevice.id')

    #: The date when we start working with this provider
    open_contract_date = DateTimeCol()

    #
    # IDescribable
    #

    def get_description(self):
        return self.short_name

    #
    # Public API
    #

    @classmethod
    def get_provider_by_provider_id(cls, provider_id, store):
        """Get a provider given a provider id string
        :param provider_id: a string representing the provider
        :param store: a database store
        """
        return store.find(cls, provider_id=provider_id)

    @classmethod
    def get_card_providers(cls, store):
        """Get a list of all credit card providers.
        :param store: a database store
        """
        return store.find(cls)

    @classmethod
    def has_card_provider(cls, store):
        """Find out if there is a card provider
        :param store: a database store
        :returns: if there is a card provider
        """
        return bool(store.find(cls).count())


@implementer(IDescribable)
class CardPaymentDevice(Domain):
    """An eletronic device used to charge the client.

    Each device may have different costs for the company, depending on the
    contract between them.

    These costs should be configured using |cardcost|
    """

    __storm_table__ = 'card_payment_device'

    #: How much the it costs the shop per month to have this device
    monthly_cost = PriceCol()

    #: user-defined description of the device, like "Mastercard reader"
    description = UnicodeCol()

    def get_description(self):
        return self.description

    def get_provider_cost(self, provider, card_type, installments):
        query = And(CardOperationCost.device_id == self.id,
                    CardOperationCost.provider_id == provider.id,
                    CardOperationCost.card_type == card_type,
                    CardOperationCost.installment_start <= installments,
                    CardOperationCost.installment_end >= installments)
        return self.store.find(CardOperationCost, query).one()

    def get_all_costs(self):
        return self.store.find(CardOperationCost, device=self)

    @classmethod
    def get_devices(cls, store):
        return store.find(cls)

    @classmethod
    def delete(cls, id, store):
        """Removes a device from the database.

        Since devices may be referenced by |cardcost| and
        |creditcarddata| objects, this method will also:

            * Remove all |cardcost| objects
            * Update all references to this device by |creditcarddata| objects
              to ``None``.
        """
        CardOperationCost.delete_from_device(id, store)

        vals = {CreditCardData.device_id: None}
        clause = CreditCardData.device_id == id
        store.execute(Update(vals, clause, CreditCardData))
        store.remove(store.get(cls, id))


class CardOperationCost(Domain):
    """The cost of a given operation on the |carddevice|

    The cost of an operation depend on the following parameters:

    * The |carddevice| that was used
    * The |creditprovider| of the card
    * The type of the card (ie, credit, debit, etc..)
    * The number of installments
    """

    __storm_table__ = 'card_operation_cost'

    device_id = IdCol(default=None)

    #: The card device used to charge the client
    device = Reference(device_id, 'CardPaymentDevice.id')

    provider_id = IdCol(default=None)

    #: The credit provider of the card
    provider = Reference(provider_id, 'CreditProvider.id')

    # One of CreditCardData.TYPE_*
    card_type = EnumCol(allow_none=False, default=u'credit')

    #: When paid in installments, this fee and fare will only apply if the
    #: installments number is in the range defined by installment_start and
    #: installment_end
    installment_start = IntCol(default=1)
    #: See :obj:`.installment_start`
    installment_end = IntCol(default=1)

    #: How many days the |creditprovider| takes to transfer the shop the money for
    #: one |payment|
    payment_days = IntCol(default=30)

    #: The percentage of each |payment| value that will be charged by the
    #: |creditprovider|
    fee = PercentCol(default=0)

    #: This is a fixed currency value that is charged for each |payment|
    fare = PriceCol(default=0)

    #
    #   Properties
    #

    def get_description(self):
        type_desc = CreditCardData.short_desc[self.card_type]
        desc = u'%s %s' % (self.provider.short_name, type_desc)
        return desc

    @property
    def installment_range_as_string(self):
        """A string representation of the installments range
        """
        inst_type = [CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE,
                     CreditCardData.TYPE_CREDIT_INSTALLMENTS_PROVIDER]
        if self.card_type not in inst_type:
            return u''
        return _(u'From %d to %d') % (self.installment_start,
                                      self.installment_end)

    @classmethod
    def delete_from_device(cls, device_id, store):
        store.execute(Delete(cls.device_id == device_id, cls))

    @classmethod
    def validate_installment_range(cls, device, provider, card_type, start, end,
                                   store, ignore=None):
        """Checks if a given range is not conflicting with any other operation cost

        :param device: the |carddevice| that will be used
        :param provider: the |creditprovider| related to the cost
        :param card_type: the car type (credit, debit, etc...)
        :param start: the start of the installment range
        :param end: the end of the installment range
        :param ignore: if not ``None``, should be an id of a |cardcost| that
          should be ignored in the query (ie, the object currently being
          edited).

        :returns: ``True`` the range is valid for the given parameters. A valid
          range means that for every possible installment value in the given
          range, there are no other |cardcost| objects that matches the
          installment value.
        """
        assert start <= end, (start, end)

        # For each possible value in the range, we want to see if there is any
        # other operation cost that already include this value.
        # range() end is non inclusive, hence the +1
        exprs = []
        for i in range(start, end + 1):
            # start <= i <= end
            inst_query = And(CardOperationCost.installment_start <= i,
                             i <= CardOperationCost.installment_end)
            exprs.append(inst_query)

        query = And(CardOperationCost.device == device,
                    CardOperationCost.card_type == card_type,
                    CardOperationCost.provider == provider,
                    Or(*exprs))

        if ignore is not None:
            query = And(query, CardOperationCost.id != ignore)

        # For this range to be valid, there should be object matching the
        # criteria above
        return store.find(cls, query).is_empty()


class CreditCardData(Domain):
    """Stores CreditCard specific state related to a payment

    This state include:

    * The type of the card used
    * The |creditprovider| of the card
    * The |carddevice| used to charge the user
    * The costs (fare an fee) that the shop was charged from the
      |creditprovider| for this payment
    """

    __storm_table__ = 'credit_card_data'

    #: Credit card payment, single installment
    TYPE_CREDIT = u'credit'

    #: Debit card payment
    TYPE_DEBIT = u'debit'

    #: Credit card payment with two or more installments.
    #: In this case, the shop is responsible for the installments, and will
    #: receive one payment each month
    TYPE_CREDIT_INSTALLMENTS_STORE = u'credit-inst-store'

    #: Credit card payment with two or more installments.
    #: In this case, the credit provider is responsible for the installments and
    #: the shop will receive the value in only one payment
    TYPE_CREDIT_INSTALLMENTS_PROVIDER = u'credit-inst-provider'

    #: This is a debit card payment, but will be charged on a pre-defined future
    #: date. Not completely supported in Stoq yet
    TYPE_DEBIT_PRE_DATED = u'debit-pre-dated'

    types = collections.OrderedDict([
        (TYPE_CREDIT, _(u'Credit Card')),
        (TYPE_DEBIT, _(u'Debit Card')),
        (TYPE_CREDIT_INSTALLMENTS_STORE, _(u'Credit Card Installments Store')),
        (TYPE_CREDIT_INSTALLMENTS_PROVIDER, _(u'Credit Card Installments '
                                              u'Provider')),
        (TYPE_DEBIT_PRE_DATED, _(u'Debit Card Pre-dated')),
    ])

    short_desc = {
        TYPE_CREDIT: _(u'Credit'),
        TYPE_DEBIT: _(u'Debit'),
        # translators: This is 'Credit Card Installments Store, but should be
        # abbreviated to fit a small space
        TYPE_CREDIT_INSTALLMENTS_STORE: _(u'Credit Inst. Store'),
        # translators: This is 'Credit Card Installments Provider, but should be
        # abbreviated to fit a small space
        TYPE_CREDIT_INSTALLMENTS_PROVIDER: _(u'Credit Inst. Provider'),
        TYPE_DEBIT_PRE_DATED: _(u'Debit Pre-dated'),
    }

    payment_id = IdCol()

    #: the |payment| this information is about
    payment = Reference(payment_id, 'Payment.id')

    card_type = EnumCol(default=TYPE_CREDIT)

    provider_id = IdCol(default=None)

    #: the |creditprovider| for this class
    provider = Reference(provider_id, 'CreditProvider.id')

    device_id = IdCol(default=None)
    #: the |carddevice| used for the payment
    #: If the |carddevice| is excluded in the future, this value will be set to null.
    device = Reference(device_id, 'CardPaymentDevice.id')

    #: the fixed value that will be charged for the related |payment|
    fare = PriceCol(default=0)

    #: the percentage of the value that will be charged for the related |payment|
    fee = PercentCol(default=0)

    #: the fee that will be charged based on the :obj:`.fee`
    fee_value = PriceCol(default=0)

    #: this is used by the tef plugin.
    nsu = IntCol(default=None)

    #: The authorization number returned by the payment device. This will be
    #: returned automatically by the tef plugin, but needs to be manually
    #: informed if not using the plugin.
    auth = IntCol(default=None)

    #: the number of installments, used by the tef plugin
    installments = IntCol(default=1)

    #: the value of the first installment (when installments > 1), used by the
    #: tef plugin
    entrance_value = PriceCol(default=0)

    def update_card_data(self, device, provider,
                         card_type, installments):
        """Creates a new |cardcost| based on |carddevice|, |creditprovider|,
        card_type and installments to update |creditcarddata|.

        :param device: the payment device
        :param provider: the credit provider
        :param card_type: the type of card, may be either credit or debit
        :param installments: the number of installments
        """

        if device is None or not isinstance(device, CardPaymentDevice):
            raise TypeError("device must be CardPaymentDevice instance and "
                            "not %r" % (device, ))
        if provider is None or not isinstance(provider, CreditProvider):
            raise TypeError("provider must be CreditProvider instance and"
                            " not %r" % (provider, ))
        if card_type is None:
            raise ValueError("card_type cannot be None")
        if installments is None:
            raise ValueError("installments cannot be None")

        cost = device.get_provider_cost(provider=provider,
                                        card_type=card_type,
                                        installments=installments)
        self.device = device
        self.provider = provider
        self.card_type = card_type

        self.fee = cost.fee if cost else 0
        self.fare = cost.fare if cost else 0

        self.fee_value = self.fee * self.payment.value / 100
