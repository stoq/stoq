# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.payment.card import CardPaymentDevice, CreditCardData
from stoqlib.domain.payment.card import CreditProvider, CardOperationCost


class TestCreditProvider(DomainTest):
    def test_has_providers(self):
        self.clean_domain([CreditProvider])
        self.assertFalse(CreditProvider.has_card_provider(self.store))

        self.create_credit_provider()
        self.assertTrue(CreditProvider.has_card_provider(self.store))

    def test_get_providers(self):
        self.clean_domain([CreditProvider])

        # Initialy no providers are present
        self.assertEquals(CreditProvider.get_card_providers(self.store).count(), 0)

        # Create one
        provider = self.create_credit_provider()

        # It should be fetched from the database
        providers = CreditProvider.get_card_providers(self.store)
        self.assertEquals(providers.count(), 1)
        self.assertEquals(providers[0], provider)

    def test_get_provider_by_id(self):
        provider = self.create_credit_provider()
        provider.provider_id = 'foo'

        obj = CreditProvider.get_provider_by_provider_id('foo', self.store)
        self.assertEquals(provider, obj[0])

    def test_get_description(self):
        provider = self.create_credit_provider('Amex')
        self.assertEquals(provider.get_description(), 'Amex')


class TestCardPaymentDevice(DomainTest):

    def test_get_description(self):
        device = self.create_card_device('Cielo')
        self.assertEquals(device.get_description(), 'Cielo')

    def test_get_prodiver_cost(self):
        credit = CreditCardData.TYPE_CREDIT
        debit = CreditCardData.TYPE_DEBIT
        device = self.create_card_device()
        provider = self.create_credit_provider()

        # There is no cost configured for this device yet
        cost = device.get_provider_cost(provider, credit, installments=1)
        self.assertEquals(cost, None)

        # Lets create a debit card cost and a cost for another provider
        self.create_operation_cost(device, provider, debit)
        provider2 = self.create_credit_provider('Foo')
        self.create_operation_cost(device, provider2, credit)

        # Cost for credit should still be None
        cost = device.get_provider_cost(provider, credit, installments=1)
        self.assertEquals(cost, None)

        cost = self.create_operation_cost(device, provider, credit)
        db_cost = device.get_provider_cost(provider, credit, installments=1)
        self.assertEquals(cost, db_cost)

    def test_get_devices(self):
        self.clean_domain([CardPaymentDevice])
        self.assertEquals(CardPaymentDevice.get_devices(self.store).count(), 0)
        device = self.create_card_device('Cielo')

        devices = list(CardPaymentDevice.get_devices(self.store))
        self.assertEquals(len(devices), 1)
        self.assertEquals(devices[0], device)

    def test_delete(self):
        self.clean_domain([CreditCardData])
        device = self.create_card_device()

        # Create an operaton cost and a card payment for this device
        self.create_operation_cost(device)
        self.create_card_payment(device=device)

        # As we created above, there should be one cost and one credit card data
        self.assertEquals(device.get_all_costs().count(), 1)
        card_data = self.store.find(CreditCardData)
        self.assertEquals(card_data.count(), 1)

        # and the card_data should reference the device
        self.assertEquals(card_data[0].device, device)

        # Now delete the device
        CardPaymentDevice.delete(device.id, self.store)

        # The operation cost should be removed...
        self.assertEquals(device.get_all_costs().count(), 0)

        # ... and the CreditCardData should still exist
        card_data = self.store.find(CreditCardData)
        self.assertEquals(card_data.count(), 1)

        # ... but does not contain a reference to the device anymore
        self.assertEquals(card_data[0].device, None)


class TestOperationCost(DomainTest):

    def test_get_description(self):
        provider = self.create_credit_provider('Visanet')
        cost = self.create_operation_cost(provider=provider,
                                    card_type=CreditCardData.TYPE_CREDIT)
        self.assertEquals(cost.get_description(), 'Visanet Credit')

    def test_installments_range(self):
        # This property is only set for installments payment (provider or store)
        cost = self.create_operation_cost(start=1, end=3,
                     card_type=CreditCardData.TYPE_CREDIT)
        self.assertEquals(cost.installment_range_as_string, '')

        cost = self.create_operation_cost(start=3, end=8,
                     card_type=CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE)
        self.assertEquals(cost.installment_range_as_string, 'From 3 to 8')

    def test_validate_installment_range(self):
        provider = self.create_credit_provider()
        device = self.create_card_device()

        # there is no other operation cost yet. Complete range should be valid
        self.assertTrue(
            CardOperationCost.validate_installment_range(device, provider,
                CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE, 1, 12, self.store))

        # Create one cost
        cost = self.create_operation_cost(start=3, end=5,
                     card_type=CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE,
                     provider=provider, device=device)

        # Test a few valid ranges:
        valid_ranges = [(1, 1), (1, 2), (2, 2), (6, 6), (6, 10), (8, 10)]
        for start, end in valid_ranges:
            self.assertTrue(
                CardOperationCost.validate_installment_range(device, provider,
                    CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE, start, end,
                    self.store))

        # now test a few invalid ranges:
        invalid_ranges = [(1, 3), (1, 4), (1, 12), (2, 3), (2, 6), (3, 3),
                          (4, 4), (4, 6)]
        for start, end in invalid_ranges:
            self.assertFalse(
                CardOperationCost.validate_installment_range(device, provider,
                    CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE, start, end,
                    self.store))

        # Also test the ignore parameter. All values above should be valid
        for start, end in invalid_ranges + valid_ranges:
            self.assertTrue(
                CardOperationCost.validate_installment_range(device, provider,
                    CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE, start, end,
                    self.store, ignore=cost.id))
