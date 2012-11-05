# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2012 Async Open Source <http://www.async.com.br>
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

from stoqlib.lib.decorators import public

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


@public(since="1.5.0")
class DeliveryStatusChangedEvent(Event):
    """
    This event is emitted when a |delivery| has it's status changed

    :param delivery: the |delivery| which had it's status changed
    :param old_status: the old delivery status
    """


class ECFIsLastSaleEvent(Event):
    """
    This event is emitted to compare the last |sale| with the last document
    in ECF.

    :param sale: |sale| that will be compared.
    """

#
# Payment related events
#


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
    """


class GerencialReportCancelEvent(Event):
    """
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
    :param conn: database connection
    """


@public(since="1.5.0")
class HasOpenCouponEvent(Event):
    """
    This event is emitted to check for opened coupon.
    """
