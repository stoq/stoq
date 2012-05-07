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
from twisted.internet.defer import (inlineCallbacks, returnValue,
                                    maybeDeferred)
from twisted.web.xmlrpc import Fault

from stoqlib.database.orm import (IntCol, UnicodeCol, BoolCol, ForeignKey,
                                  SingleJoin)
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.sale import Sale, Delivery
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

from domain.magentobase import MagentoBaseSyncUp, MagentoBaseSyncBoth
from domain.magentoclient import MagentoClient, MagentoAddress
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

    status = UnicodeCol(default=STATUS_NEW)
    sale = ForeignKey('Sale', default=None)
    can_deliver = BoolCol(default=False)
    magento_client = ForeignKey('MagentoClient', default=None)
    magento_address = ForeignKey('MagentoAddress', default=None)

    magento_invoice = SingleJoin('MagentoInvoice',
                                 joinColumn='magento_sale_id')
    magento_delivery = SingleJoin('MagentoShipment',
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

    @inlineCallbacks
    def add_comment_remote(self, msg, notify_user=True):
        data = [self.magento_id, self.status, msg, notify_user]

        try:
            retval = yield self.proxy.call('order.addComment', data)
        except Fault as err:
            log.error("An error occurred when trying to add a comment on a "
                      "sale on Magento: %s" % err.faultString)
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

        for item in info['items']:
            mag_product = MagentoProduct.selectOneBy(connection=conn,
                                                     config=self.config,
                                                     sku=item['sku'])
            if not mag_product:
                log.error("Unexpected error: Could not find the magento "
                          "product by sku %s. It should be synchronized "
                          "at this point" % item['sku'])
                return False

            sellable = mag_product.sellable
            if sellable.product:
                # If we have at least one product, we can deliver it.
                self.can_deliver = True

            price = item['price']
            quantity = item['qty_ordered']

            self.sale.add_sellable(sellable,
                                   quantity=quantity,
                                   price=price)

        if self.can_deliver:
            delivery_service = sysparam_.DELIVERY_SERVICE
            delivery_price = info['shipping_amount'] or 0
            self.sale.add_sellable(delivery_service.sellable,
                                   price=delivery_price)

        method = PaymentMethod.get_by_name(conn, 'online')
        # Till needs to be None, or else, it will try to get the current one,
        # which doesn't exists on daemon
        method.create_inpayment(group, info['grand_total'], till=None)

        self.sale.order()

        return self.update_local(info)

    def update_local(self, info):
        conn = self.get_connection()
        if self.can_deliver and not self.magento_address:
            mag_address_id = (info['shipping_address']['customer_address_id'] or
                              info['billing_address']['customer_address_id'])
            mag_address = MagentoAddress.selectOneBy(
                connection=conn,
                config=self.config,
                magento_id=mag_address_id,
                )
            if not mag_address:
                log.error("Unexpected error: Could not find the magento "
                          "address by id %s. It should be synchronized "
                          "at this point" % (mag_address_id,))
                return False

            self.magento_address = mag_address

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
            if self.can_deliver:
                retval = self._create_delivery()
            else:
                retval = True
        elif (self.sale.status in (Sale.STATUS_CANCELLED, Sale.STATUS_RETURNED)
              and self.status != self.STATUS_CANCELLED):
            # FIXME: If the sale was already invoiced on Magento, it's
            #        unlikly it will let us cancel it. Maybe we should
            #        avoid that on Stoq.
            retval = yield self.cancel_remote()
            if not retval:
                returnValue(False)

        returnValue(True)

    #
    #  Private
    #

    def _create_delivery(self):
        if self.magento_delivery:
            return True

        conn = self.get_connection()
        sysparam_ = sysparam(conn)
        sale_items = set(self.sale.get_items())

        service_item = None
        delivery_sellable = sysparam_.DELIVERY_SERVICE.sellable
        # Use list here, or we will have a RuntimeError when set changes size
        for item in list(sale_items):
            sellable = item.sellable
            if sellable.service:
                if sellable == delivery_sellable:
                    service_item = item
                # Stoq does not deliver services
                sale_items.remove(item)
                continue

        delivery = Delivery(connection=conn,
                            address=self.magento_address.address,
                            service_item=service_item,
                            transporter=self.sale.transporter)
        for item in sale_items:
            delivery.add_item(item)

        mag_delivery = MagentoShipment(connection=conn,
                                       config=self.config,
                                       magento_sale=self,
                                       delivery=delivery)

        return bool(mag_delivery)


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
        return not self.magento_sale

    def create_local(self, info):
        conn = self.get_connection()
        mag_sale_id = info['order_increment_id']
        mag_sale = MagentoSale.selectOneBy(connection=conn,
                                           config=self.config,
                                           magento_id=mag_sale_id)
        if not mag_sale:
            log.error("Unexpected error: Could not find the magento sale by "
                      "id %s. It should be synchronized at this point" %
                      (mag_sale_id,))
            return False

        self.magento_sale = mag_sale
        if info['state'] == self.STATUS_OPEN:
            # Make sure we will try to capture the invoice online
            self.keep_need_sync = True

        return self.update_local(info)

    def update_local(self, info):
        self.status = info['state']
        self.can_void = bool(info['can_void_flag'])

        table_config = self.config.get_table_config(self.__class__)
        # Update this by hand since this isn't visible on list.
        # See MagentoBaseSyncDown.synchronize for more information
        table_config.last_sync_date = max(table_config.last_sync_date,
                                          info['updated_at'])

        sale = self.magento_sale.sale
        if (self.status == self.STATUS_PAID and
            sale.status != Sale.STATUS_PAID):
            if not sale.can_set_paid():
                # The sale wasn't confirmed yet. Wait until it's confirmed,
                # and then mark it as paid.
                self.keep_need_sync = True
                return True

            if not sale.group.status == PaymentGroup.STATUS_PAID:
                sale.group.pay()
            sale.set_paid()
            self.magento_sale.need_sync = True
        elif (self.status == self.STATUS_CANCELLED and
              sale.status != Sale.STATUS_CANCELLED):
            # The payment was cancelled on gateway the gateway.
            # Cancel it on Stoq too.
            if sale.group.can_cancel():
                sale.group.cancel()
            self.sale.cancel()

        return True

    #
    #  MagentoBaseSyncUp hooks
    #

    @inlineCallbacks
    def create_remote(self):
        magento_id = self.magento_sale.magento_id
        comment = ''
        include_comment = True
        send_email = False

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
    delivery = ForeignKey('Delivery')
    magento_sale = ForeignKey('MagentoSale', default=None)

    #
    #  Public API
    #

    @inlineCallbacks
    def add_track_remote(self):
        magento_id = self.magento_id
        # FIXME: Should we inform the track_service? If yes, we need to add
        #        that kind of support on Delivery
        transporter = self.delivery.transporter
        transporter = transporter.get_description() if transporter else ''
        track_service = ''
        track_number = self.delivery.tracking_code

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
        if self.delivery.status == Delivery.STATUS_INITIAL:
            # Fool the syncdaemon. When delivery change status, since we
            # still don't have a magento_id, it will come back here again.
            returnValue(True)

        magento_id = self.magento_sale.magento_id
        comment = ''
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
        retval = True

        if not self.was_track_added:
            # FIXME: Can't add track for now. See FIXME note on method
            returnValue(retval)
            retval = yield self.add_track_remote()
            self.was_track_added = retval
            self.keep_need_sync = not retval

        returnValue(retval)
