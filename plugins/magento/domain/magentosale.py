# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from kiwi.log import Logger
from twisted.internet.defer import (inlineCallbacks, returnValue, succeed,
                                    maybeDeferred)
from twisted.web.xmlrpc import Fault

from stoqlib.database.orm import (IntCol, UnicodeCol, BoolCol, ForeignKey,
                                  SingleJoin)
from stoqlib.domain.interfaces import IDelivery
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.sale import Sale, DeliveryItem
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

from domain.magentobase import MagentoBaseSyncUp, MagentoBaseSyncBoth
from domain.magentoclient import MagentoClient
from domain.magentoproduct import MagentoProduct

_ = stoqlib_gettext
log = Logger('plugins.magento.domain.magentosale')


class MagentoSale(MagentoBaseSyncBoth):
    """Class for sale synchronization between Stoq and Magento"""

    API_NAME = 'order'
    API_ID_NAME = 'increment_id'

    (ERROR_SALE_NOT_EXISTS,
     ERROR_SALE_INVALID_FILTERS,
     ERROR_SALE_INVALID_DATA,
     ERROR_SALE_STATUS_NOT_CHANGED) = range(100, 104)

    STATUS_NEW = 'new'
    STATUS_PROCESSING = 'processing'
    STATUS_CANCELLED = 'canceled'
    STATUS_CLOSED = 'closed'
    STATUS_COMPLETE = 'complete'
    STATUS_HOLDED = 'holded'
    STATUS_PAYMENT_REVIEW = 'payment_review'
    STATUS_PENDING_PAYMENT = 'pending_payment'

    # Is there a way to differentiate check from money? Magento doesn't
    PAYMENT_METHOD_MONEY = 'checkmo'
    PAYMENT_METHOD_CARD = 'ccsave'

    status = UnicodeCol(default=STATUS_NEW)
    sale = ForeignKey('Sale', default=None)
    magento_client = ForeignKey('MagentoClient', default=None)

    magento_invoice = SingleJoin('MagentoInvoice',
                                 joinColumn='magento_sale_id')

    #
    #  Public API
    #

    @inlineCallbacks
    def cancel_remote(self):
        mag_invoice = self.magento_invoice
        if mag_invoice:
            retval = yield mag_invoice.cancel_remote()
            if not retval:
                returnValue(False)

        try:
            retval = yield self.proxy.call('order.cancel', [self.magento_id])
        except Fault as err:
            log.error("An error occurred when trying to cancel a sale on "
                      "Magento: %s" % err.faultString)
            returnValue(False)

        returnValue(retval)

    @inlineCallbacks
    def hold_remote(self):
        try:
            retval = yield self.proxy.call('order.hold', [self.magento_id])
        except Fault as err:
            log.error("An error occurred when trying to hold a sale on "
                      "Magento: %s" % err.faultString)
            returnValue(False)

        returnValue(retval)

    @inlineCallbacks
    def unhold_remote(self):
        try:
            retval = yield self.proxy.call('order.unhold', [self.magento_id])
        except Fault as err:
            log.error("An error occurred when trying to unhold a sale on "
                      "Magento: %s" % err.faultString)
            returnValue(False)

        returnValue(retval)

    #
    #  MagentoBaseSyncDown hooks
    #

    def need_create_local(self):
        return not self.sale

    def create_local(self, info):
        assert self.need_create_local()

        conn = self.get_connection()
        sysparam_ = sysparam(conn)

        if not self.magento_client:
            mag_client_id = info[MagentoClient.API_ID_NAME]
            mag_client = MagentoClient.selectOneBy(connection=conn,
                                                   config=self.config,
                                                   magento_id=mag_client_id)
            if not mag_client:
                log.error("Unexpected error: Could not find the magento "
                          "client by id %s. It should be synchronized "
                          "at this point" % mag_client_id)
                return False
            elif mag_client and not mag_client.client:
                # Wait until mag_client has a real client (sync sucessful)
                return False

            self.magento_client = mag_client

        client = self.magento_client.client
        branch = self.config.branch
        salesperson = self.config.salesperson
        operation_nature = sysparam_.DEFAULT_OPERATION_NATURE
        group = PaymentGroup(connection=conn)
        open_date = info['created_at']
        total_amount = info['grand_total']
        notes = _("Magento sale #%s\n") % self.magento_id

        self.sale = Sale(connection=conn,
                         client=client,
                         branch=branch,
                         salesperson=salesperson,
                         operation_nature=operation_nature,
                         group=group,
                         open_date=open_date,
                         total_amount=total_amount,
                         notes=notes,
                         coupon_id=None)

        mag_address = info['shipping_address']
        address = "%s\n%s\n%s - %s" % (mag_address['street'] or '',
                                       mag_address['postcode'] or '',
                                       mag_address['city'] or '',
                                       mag_address['region'] or '')

        delivery_service = sysparam_.DELIVERY_SERVICE
        delivery_price = info['shipping_amount'] or 0
        self.sale.add_sellable(delivery_service.sellable,
                               price=delivery_price)

        for item in info['items']:
            mag_product = MagentoProduct.selectOneBy(connection=conn,
                                                     config=self.config,
                                                     sku=item['sku'])
            if not mag_product:
                log.error("Unexpected error: Could not find the magento "
                          "product by sku %s. It should be synchronized "
                          "at this point" % item['sku'])
                return False

            sellable = mag_product.product.sellable
            price = item['price']
            quantity = item['qty_ordered']

            sale_item = self.sale.add_sellable(sellable,
                                               quantity=quantity,
                                               price=price)

            DeliveryItem.create_from_sellable_item(sale_item)
            delivery = sale_item.addFacet(IDelivery,
                                          connection=conn)
            delivery.address = address

        payment_info = info['payment']
        payment_method = payment_info['method']

        if payment_method == self.PAYMENT_METHOD_MONEY:
            method_name = 'money'
        elif payment_method == self.PAYMENT_METHOD_CARD:
            method_name = 'card'
        else:
            log.error("Unknow payment method: %s" % payment_method)
            return False

        register_payment_operations()
        method = PaymentMethod.get_by_name(conn, method_name)
        method.create_inpayment(group, info['grand_total'])

        self.sale.order()

        return self.update_local(info)

    def update_local(self, info):
        self.status = info['status']

        return True

    #
    #  MagentoBaseSyncUp hooks
    #

    def need_create_remote(self):
        # Sales come from Magento, not the other way
        return False

    @inlineCallbacks
    def update_remote(self):
        assert not self.need_create_local()
        conn = self.get_connection()

        if self.sale.status == Sale.STATUS_PAID:
            if not self.magento_invoice:
                # Just creating. It'll be syncronized soon
                MagentoInvoice(connection=conn,
                               config=self.config,
                               magento_sale=self)
        elif (self.sale.status == Sale.STATUS_CANCELLED and
              self.status != self.STATUS_CANCELLED):
            # FIXME: If the sale was already invoiced on Magento, it's
            #        unlikly it will let us cancel it. Maybe we should
            #        avoid that on Stoq.
            retval = yield self.cancel_remote()
            if not retval:
                returnValue(False)

        returnValue(True)


class MagentoInvoice(MagentoBaseSyncBoth):
    """Class for sale invoice synchronization between Stoq and Magento"""

    API_NAME = 'order_invoice'
    API_ID_NAME = 'increment_id'

    (STATUS_OPEN,
     STATUS_PAID,
     STATUS_CANCELLED) = range(1, 4)

    (ERROR_INVOICE_NOT_EXISTS,
     ERROR_INVOICE_INVALID_FILTERS,
     ERROR_INVOICE_INVALID_DATA,
     ERROR_INVOICE_SALE_NOT_EXISTS,
     ERROR_INVOICE_STATUS_NOT_CHANGED) = range(100, 105)

    status = IntCol(default=STATUS_OPEN)
    can_void = BoolCol(default=False)
    magento_sale = ForeignKey('MagentoSale', default=None)

    #
    #  Public API
    #

    @inlineCallbacks
    def cancel_remote(self):
        if self.can_void:
            retval = yield self.void_remote()
            returnValue(retval)

        magento_id = self.magento_id
        try:
            retval = yield self.proxy.call('order_invoice.cancel',
                                           [magento_id])
        except Fault as err:
            log.error("An error occurred when trying to cancel an invoice for "
                      "sale %s on Magento: %s" % (magento_id, err.faultString))
            returnValue(False)

        returnValue(retval)

    @inlineCallbacks
    def capture_remote(self):
        magento_id = self.magento_id
        try:
            retval = yield self.proxy.call('order_invoice.capture',
                                           [magento_id])
        except Fault as err:
            log.error("An error occurred when trying to capture an invoice for "
                      "sale %s on Magento: %s" % (magento_id, err.faultString))
            returnValue(False)

        returnValue(retval)

    @inlineCallbacks
    def void_remote(self):
        assert self.can_void

        magento_id = self.magento_id
        try:
            retval = yield self.proxy.call('order_invoice.void', [magento_id])
        except Fault as err:
            log.error("An error occurred when trying to void an invoice for "
                      "sale %s on Magento: %s" % (magento_id, err.faultString))
            returnValue(False)

        returnValue(retval)

    #
    #  MagentoBase hooks
    #

    @classmethod
    def list_remote(cls, *args, **kwargs):
        # There's not need to import invoices, since we create them on
        # MagentoSale. We only need to update it's info.
        return succeed([])

    @inlineCallbacks
    def process(self, **kwargs):
        if not self.magento_id:
            # We first need to sync up, creating the invoice on Magento. After
            # that, it's ok to do both syncs.
            kwargs['sync_down'] = False
            self.keep_need_sync = True

        retval = yield maybeDeferred(super(MagentoInvoice, self).process,
                                     **kwargs)
        returnValue(retval)

    #
    #  MagentoBaseSyncDown hooks
    #

    def need_create_local(self):
        # We dont import invoices.
        return False

    def update_local(self, info):
        self.status = info['state']
        self.can_void = bool(info['can_void_flag'])

        return True

    #
    #  MagentoBaseSyncUp hooks
    #

    @inlineCallbacks
    def create_remote(self):
        magento_id = self.magento_sale.magento_id
        comment = _("Invoice for order: %s") % self.magento_id
        include_comment = True
        send_email = True

        # [] means all products will be invoiced.
        data = [magento_id, [], comment, send_email, include_comment]
        try:
            retval = yield self.proxy.call('order_invoice.create', data)
        except Fault as err:
            log.error("An error occurred when trying to create an invoice for "
                      "sale %s on Magento: %s" % (magento_id, err.faultString))
            returnValue(False)
        else:
            self.magento_id = retval

        returnValue(bool(retval))

    @inlineCallbacks
    def update_remote(self):
        if self.status == self.STATUS_OPEN:
            # self.create_remote should have marked invoice as paid. If not,
            # that probably means the invoice can be captured online.
            retval = yield self.capture_remote()
            # If captured, self.status will be updated on next sync. Just make
            # sure that next sync will happen.
            self.keep_need_sync = True
        else:
            retval = True

        returnValue(retval)


class MagentoShipment(MagentoBaseSyncUp):
    """Class for sale shipment synchronization between Stoq and Magento"""

    API_NAME = 'order_shipment'
    API_ID_NAME = 'increment_id'

    (ERROR_SHIPMENT_NOT_EXISTS,
     ERROR_SHIPMENT_INVALID_FILTERS,
     ERROR_SHIPMENT_INVALID_DATA,
     ERROR_SHIPMENT_SALE_NOT_EXISTS,
     ERROR_SHIPMENT_STATUS_NOT_CHANGED,
     ERROR_SHIPMENT_TRACKING_NOT_DELETED) = range(100, 106)

    was_track_added = BoolCol(default=False)
    magento_sale = ForeignKey('MagentoSale', default=None)

    #
    #  Public API
    #

    @inlineCallbacks
    def add_track_remote(self):
        magento_id = self.magento_id
        # FIXME: The transporter needs to be registered on magento first.
        #        How to do that?
        transporter = self.magento_sale.sale.transporter
        transporter = transporter and transporter.name
        # FIXME: Get the track service and number from delivery.
        #        Waiting for some support on SaleItemAdaptToDelivery
        track_service = 'SEDEX'
        track_number = 'BR1234567890'

        data = [magento_id, transporter, track_service, track_number]
        try:
            retval = yield self.proxy.call('order_shipment.addTrack', data)
        except Fault as err:
            log.error("An error occurred when trying to add a track for "
                      "shipment %s on Magento: %s" % (magento_id,
                                                      err.faultString))
            returnValue(False)

        returnValue(bool(retval))

    #
    #  MagentoBaseSyncUp hooks
    #

    @inlineCallbacks
    def create_remote(self):
        magento_id = self.magento_sale.magento_id
        comment = _("Shipment for order: %s") % self.magento_id
        include_comment = True
        send_email = True

        # [] means all products will be shipped.
        data = [magento_id, [], comment, send_email, include_comment]
        try:
            retval = yield self.proxy.call('order_shipment.create', data)
        except Fault as err:
            log.error("An error occurred when trying to create a shipment for "
                      "sale %s on Magento: %s" % (magento_id, err.faultString))
            returnValue(False)
        else:
            self.magento_id = retval

        # Make sure we will call update on next sync. We could call here but
        # if it fails, the sync process will try to create the shipment again.
        self.keep_need_sync = True

        returnValue(bool(retval))

    @inlineCallbacks
    def update_remote(self):
        if not self.was_track_added:
            retval = yield self.add_track_remote()
            self.was_track_added = retval

        returnValue(retval)
