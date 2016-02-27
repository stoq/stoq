# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2014 Async Open Source <http://www.async.com.br>
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

"""
Events used in the domain code
"""

# pylint: enable=E1101

from stoqlib.enums import CreatePaymentStatus
from stoqlib.lib.event import Event
from stoqlib.lib.decorators import public

#
# Base domain events
#


@public(since="1.9.0")
class DomainMergeEvent(Event):
    """
    This event is emitted two domain objects are being merged

    :param obj: the main object that is being merged with (the one that will be kept)
    :param other: the object that is being merged. This is the one that will
      have the references fixed
    """

    @classmethod
    def handle_return_values(self, values):
        skip = set()
        for value in values:
            if value is None:
                continue
            skip = skip.union(value)
        return skip


#
# Product events
#


@public(since="1.5.0")
class ProductCreateEvent(Event):
    """
    This event is emitted when a |product| is created.

    :param product: the created |product|
    """


@public(since="1.5.0")
class ProductEditEvent(Event):
    """
    This event is emitted when a |product| is edited.

    :param product: the edited |product|
    """


@public(since="1.5.0")
class ProductRemoveEvent(Event):
    """
    This event is emitted when a |product| is about to be removed.

    :param product: the removed |product|
    """


@public(since="1.5.0")
class ProductStockUpdateEvent(Event):
    """
    This event is emitted when a |product| stock is in/decreased.

    :param product: the |product| that had it's stock modified
    :param branch: the |branch| on which the stock was modified
    :param old_quantity: the old product stock quantity
    :param new_quantity: the new product stock quantity
    """


class SellableCheckTaxesEvent(Event):
    """
    This event is emitted to check the sellable fiscal data.

    If the tax is not valid, one should raise `TaxError` just like
    sellable.check_tax_validity does.

    :param sellable: the |sellable| that will be checked
    """

#
# Service events
#


@public(since="1.5.0")
class ServiceCreateEvent(Event):
    """
    This event is emitted when a |service| is created.

    :param service: the created |service|
    """


@public(since="1.5.0")
class ServiceEditEvent(Event):
    """
    This event is emitted when a |service| is edited.

    :param service: the edited |service|
    """


@public(since="1.5.0")
class ServiceRemoveEvent(Event):
    """
    This event is emitted when a |service| is about to be removed.

    :param product: the removed |service|
    """


#
# Category events
#

@public(since="1.5.0")
class CategoryCreateEvent(Event):
    """
    This event is emitted when a category is created.

    :param category: the created category
    """


@public(since="1.5.0")
class CategoryEditEvent(Event):
    """
    This event is emitted when a category is edited.

    :param category: the edited category
    """


#
# Image events
#

class ImageCreateEvent(Event):
    """
    This event is emitted when an |image| is created.

    :param image: the created |image|
    """


class ImageEditEvent(Event):
    """
    This event is emitted when an |image| is edited.

    :param image: the edited |image|
    """


class ImageRemoveEvent(Event):
    """
    This event is emitted when an |image| is removed.

    :param image: the removed |image|
    """


#
# Sale events
#

class SaleStatusChangedEvent(Event):
    """
    This event is emitted when a |sale| is has it's status changed

    :param sale: the |sale| which had it's status changed
    :param old_status: the old sale status
    """


@public(since="1.8.0")
class SaleCanCancelEvent(Event):
    """
    This event is emitted to check if a |sale| can be cancelled

    The expected return should be ``True`` if the |sale| can be
    canceled, or ``False`` if it can't.

    :param sale: the |sale| that is going to be cancelled
    """


@public(since="1.9.0")
class SaleIsExternalEvent(Event):
    """Emitted to check if a |sale| is external.

    External sales are the ones done outside of the commercial
    establishment.

    The expected return value should be ``True`` if the sale
    is to be considered as external or ``False`` otherwise.

    :param sale: The sale that we want to check
    """


class SaleItemBeforeDecreaseStockEvent(Event):
    """
    This event is emitted when a |saleitem| is about to decrease the stock

    This is usually called at the beginning of
    :meth:`stoqlib.domain.sale.SaleItem.sell`

    :param sale_item: the |saleitem| object
    """


class SaleItemBeforeIncreaseStockEvent(Event):
    """
    This event is emitted when a |saleitem| is about to increase the stock

    This is usually called at the beginning of
    :meth:`stoqlib.domain.sale.SaleItem.cancel`

    :param sale_item: the |saleitem| object
    """


class SaleItemAfterSetBatchesEvent(Event):
    """
    This event is emitted after a |saleitem| set it's batches

    This is called at the end of
    :meth:`stoqlib.domain.sale.SaleItem.set_batches`

    :param sale_item: the |saleitem| object
    :param new_sale_items: a list of the new |saleitems| created
        when setting the batches
    """


@public(since="1.5.0")
class DeliveryStatusChangedEvent(Event):
    """
    This event is emitted when a |delivery| has it's status changed

    :param delivery: the |delivery| which had it's status changed
    :param old_status: the old delivery status
    """


@public(since="1.10.0")
class SaleAvoidCancelEvent(Event):
    """
    This event is emitted to compare the last |sale| with the last document
    in ECF.

    :param sale: |sale| that will be compared.
    :return: ``True`` if the cancellation should be avoided or
        ``False` otherwise
    """

#
# Payment related events
#


@public(since="1.11.0")
class PaymentGroupGetOrderEvent(Event):
    """Get the order of a payment group.

    :param group: the |paymentgroup| that we want the related order
    :param store: a store
    """


@public(since="1.5.0")
class CreatePaymentEvent(Event):
    """
    This event is emmited when a |payment| is about to be created and
    should be used to 'intercept' that payment creation.

    return value should be one of :class:`enum.CreatePaymentStatus`

    :param payment_method: The selected |payment| method.
    :param sale: The |sale| the payment should belong to
    """

    returnclass = CreatePaymentStatus


@public(since="1.5.0")
class CardPaymentReceiptPrepareEvent(Event):
    """
    This will be emmited when a card |payment| receipt should be printed.

    Expected return value is a string to be printed

    :param payment: the receipt of this |payment|
    :param supports_duplicate: if the printer being used supports duplicate
                               receipts
    """


@public(since="1.5.0")
class CardPaymentReceiptPrintedEvent(Event):
    """
    This gets emmited after a card |payment| receipt is successfully printed.

    :param payment: the receipt of this |payment|
    """


@public(since="1.5.0")
class CancelPendingPaymentsEvent(Event):
    """
    This gets emmited if a card |payment| receipt fails to be printed, meaning
    that all payments should be cancelled
    """


class GerencialReportPrintEvent(Event):
    """
    This is emitted when the user requests a gerencial report
    for fiscal printers.
    """


class GerencialReportCancelEvent(Event):
    """
    This is emitted when the user cancels a gerencial report
    for fiscal printers.
    """


@public(since="1.5.0")
class CheckECFStateEvent(Event):
    """After the TEF has initialized, we must check if the printer is
    responding. TEF plugin will emit this event for the ECF plugin
    """


#
# Till events
#

@public(since="1.5.0")
class TillOpenEvent(Event):
    """
    This event is emitted when a |till| is opened

    :param till: the opened |till|
    """


@public(since="1.5.0")
class TillCloseEvent(Event):
    """
    This event is emitted when a |till| is closed

    :param till: the closed |till|
    :param previous_day: if the |till| wasn't closed previously
    """


class HasPendingReduceZ(Event):
    """
    This event is emitted when a has pending 'reduce z' in ecf.
    """
    pass


@public(since="1.5.0")
class TillAddCashEvent(Event):
    """
    This event is emitted when cash is added to a |till|

    :param till: the closed |till|
    :param value: amount added to the |till|
    """


@public(since="1.5.0")
class TillRemoveCashEvent(Event):
    """
    This event is emitted when cash is removed from a |till|

    :param till: the closed |till|
    :param value: amount remove from the |till|
    """


@public(since="1.5.0")
class TillAddTillEntryEvent(Event):
    """
    This event is emitted when:

    * cash is added to a |till|
    * cash is removed from a |till|

    :param till_entry: a |tillentry|
    :param store: a store
    """


@public(since="1.5.0")
class HasOpenCouponEvent(Event):
    """
    This event is emitted to check for opened coupon.
    """
