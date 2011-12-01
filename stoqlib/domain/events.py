# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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

from stoqlib.enums import CreatePaymentStatus
from stoqlib.lib.event import Event

#
# Product events
#


class ProductCreateEvent(Event):
    """
    This event is emitted when a product is created.

    @param product: the created product
    """


class ProductEditEvent(Event):
    """
    This event is emitted when a product is edited.

    @param product: the edited product
    """


class ProductRemoveEvent(Event):
    """
    This event is emitted when a product is about to be removed.

    @param product: the removed product
    """


class ProductStockUpdateEvent(Event):
    """
    This event is emitted when a product stock is in/decreased.

    @param product: the product that had it's stock modified
    @param branch: the branch on which the stock was modified
    @param old_quantity: the old product stock quantity
    @param new_quantity: the new product stock quantity
    """


#
# Category events
#

class CategoryCreateEvent(Event):
    """
    This event is emitted when a category is created.

    @param product: the created category
    """


class CategoryEditEvent(Event):
    """
    This event is emitted when a category is edited.

    @param product: the edited category
    """


#
# Sale events
#

class SaleStatusChangedEvent(Event):
    """
    This event is emitted when a sale is confirmed

    @param sale: the sale which had it's status changed
    @param old_status: the old sale status
    """


class ECFIsLastSaleEvent(Event):
    """
    This event is emitted to compare the last sale with the last document
    in ECF.

    @param sale: sale that will be compared.
    """

#
# Payment related events
#


class CreatePaymentEvent(Event):
    """
    This event is emmited when a payment is about to be created and
    should be used to 'intercept' that payment creation.

    return value should be one of L{enum.CreatePaymentStatus}

    @param payment_method: The selected payment method.
    @param sale: The sale the payment should belong to
    """

    returnclass = CreatePaymentStatus


class CardPaymentReceiptPrepareEvent(Event):
    """
    This will be emmited when a card payment receipt should be printed.

    Expected return value is a string to be printed

    @param payment: the receipt of this payment
    @param supports_duplicate: if the printer being used supports duplicate
                               receipts
    """


class CardPaymentReceiptPrintedEvent(Event):
    """
    This gets emmited after a card payment receipt is successfully printed.

    @param payment: the receipt of this payment
    """


class CancelPendingPaymentsEvent(Event):
    """
    This gets emmited if a card payment receipt fails to be printed, meaning
    that all payments should be cancelled
    """


class GerencialReportPrintEvent(Event):
    """
    """


class GerencialReportCancelEvent(Event):
    """
    """


class CheckECFStateEvent(Event):
    """After the TEF has initialized, we must check if the printer is
    responding. TEF plugin will emit this event for the ECF plugin
    """


#
# Till events
#

class TillOpenEvent(Event):
    """
    This event is emitted when a till is opened
    @param till: the opened till
    """


class TillCloseEvent(Event):
    """
    This event is emitted when a till is closed
    @param till: the closed till
    @param previous_day: if the till wasn't closed previously
    """


class HasPendingReduceZ(Event):
    """
    This event is emitted when a has pending 'reduce z' in ecf.
    """
    pass


class TillAddCashEvent(Event):
    """
    This event is emitted when cash is added to a till
    @param till: the closed till
    @param value: amount added to the till
    """


class TillRemoveCashEvent(Event):
    """
    This event is emitted when cash is removed from a till
    @param till: the closed till
    @param value: amount remove from the till
    """


class TillAddTillEntryEvent(Event):
    """
    This event is emitted when:

    cash is added to a till;
    cash is removed from a till;
    @param till_entry: TillEntry object
    @param conn: database connection
    """
