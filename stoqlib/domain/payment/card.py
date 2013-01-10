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

- :obj:`CreditProvider` - The institution that provided the credit for the client.
  Visanet and American Express, for instance

"""

from zope.interface import implements

from stoqlib.database.orm import PercentCol, PriceCol, DateTimeCol
from stoqlib.database.orm import IntCol, BoolCol, UnicodeCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IActive, IDescribable
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CreditProvider(Domain):
    """A credit provider
     """
    __storm_table__ = 'credit_provider'

    implements(IActive, IDescribable)

    (PROVIDER_CARD, ) = range(1)

    #: This attribute must be either provider card or provider finance
    provider_types = {PROVIDER_CARD: _(u'Card Provider')}

    is_active = BoolCol(default=True)
    provider_type = IntCol(default=PROVIDER_CARD)

    #: A short description of this provider
    short_name = UnicodeCol()

    # FIXME: Rename, remove _id suffix
    #: An identification for this provider
    provider_id = UnicodeCol(default='')

    #: The date when we start working with this provider
    open_contract_date = DateTimeCol()
    closing_day = IntCol(default=10)
    payment_day = IntCol(default=10)
    max_installments = IntCol(default=12)

    #: values charged monthly by the credit provider
    monthly_fee = PriceCol(default=0)

    #: fee applied by the provider for each payment transaction,
    #: depending on the transaction type
    credit_fee = PercentCol(default=0)

    #: see :obj:`.credit_fee`
    credit_installments_store_fee = PercentCol(default=0)

    #: see :obj:`.credit_fee`
    credit_installments_provider_fee = PercentCol(default=0)

    #: see :obj:`.credit_fee`
    debit_fee = PercentCol(default=0)

    #: see :obj:`.credit_fee`
    debit_pre_dated_fee = PercentCol(default=0)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, ('This credit provider is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, ('This credit provider is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _('Active')
        return _('Inactive')

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
        return store.find(cls, is_active=True, provider_type=cls.PROVIDER_CARD,
                          provider_id=provider_id)

    @classmethod
    def get_card_providers(cls, store):
        """Get a list of all credit card providers.
        :param store: a database store
        """
        return store.find(cls, is_active=True, provider_type=cls.PROVIDER_CARD)

    @classmethod
    def has_card_provider(cls, store):
        """Find out if there is a card provider
        :param store: a database store
        :returns: if there is a card provider
        """
        return bool(store.find(cls, is_active=True,
                               provider_type=cls.PROVIDER_CARD).count())

    @classmethod
    def get_active_providers(cls, store):
        return store.find(cls, is_active=True)

    def get_fee_for_payment(self, data):
        from stoqlib.domain.payment.method import CreditCardData
        type_property_map = {
            CreditCardData.TYPE_CREDIT: 'credit_fee',
            CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE: 'credit_installments_store_fee',
            CreditCardData.TYPE_CREDIT_INSTALLMENTS_PROVIDER: 'credit_installments_provider_fee',
            CreditCardData.TYPE_DEBIT: 'debit_fee',
            CreditCardData.TYPE_DEBIT_PRE_DATED: 'debit_pre_dated_fee'
        }
        return getattr(self, type_property_map[data.card_type])
