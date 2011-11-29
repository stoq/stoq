# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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

"""Provide tools for communication between Stoq and Magento e-commerce."""

import os
import sys

from kiwi.environ import environ
from kiwi.log import Logger
from twisted.internet.defer import DeferredLock, returnValue, inlineCallbacks
from zope.interface import implements

from stoqlib.database.migration import PluginSchemaMigration
from stoqlib.domain.events import (ProductCreateEvent, ProductRemoveEvent,
                                   ProductEditEvent, ProductStockUpdateEvent,
                                   SaleStatusChangedEvent)
from stoqlib.lib.interfaces import IPlugin
from stoqlib.lib.pluginmanager import register_plugin

plugin_root = os.path.dirname(__file__)
sys.path.append(plugin_root)
from domain.magentoclient import MagentoClient, MagentoAddress
from domain.magentoproduct import MagentoProduct, MagentoStock
from domain.magentosale import MagentoSale, MagentoInvoice, MagentoShipment

log = Logger('plugins.magento.magentoplugin')


class MagentoPlugin(object):
    """Plugin for synchronization between Stoq and Magento."""

    implements(IPlugin)

    name = 'magento'
    has_product_slave = False

    def __init__(self):
        self._lock = DeferredLock()

    #
    #  Public API
    #

    @inlineCallbacks
    def synchronize(self):
        """Wraps all magento domain C{synchronize} methods.

        @returns: C{True} if all sync went well, C{False} otherwise
        """
        # The lock is here to make sure we have only one sync running.
        yield self._lock.acquire()
        try:
            retval_list = []
            # The order above matters. e.g. We always want to sync products
            # and clients before sales, to avoid problems with references.
            for table in (MagentoProduct, MagentoStock, MagentoClient,
                          MagentoAddress, MagentoSale, MagentoInvoice,
                          MagentoShipment):
                retval = yield self._synchronize_magento_table(table)
                retval_list.append(retval)
            returnValue(all(retval_list))
        finally:
            self._lock.release()

    #
    #  IPlugin implementation
    #

    def activate(self):
        # Connect product events
        ProductCreateEvent.connect(self._on_product_create)
        ProductRemoveEvent.connect(self._on_product_delete)
        ProductEditEvent.connect(self._on_product_update)
        ProductStockUpdateEvent.connect(self._on_product_stock_update)

        # Connect sale events
        SaleStatusChangedEvent.connect(self._on_sale_status_change)

    def get_tables(self):
        return [
            ('domain.magentoconfig', ['MagentoConfig',
                                      'MagentoTableConfig'])
            ('domain.magentoproduct', ['MagentoProduct',
                                       'MagentoStock']),
            ('domain.magentoclient', ['MagentoClient',
                                      'MagentoAddress']),
            ('domain.magentosale', ['MagentoSale',
                                    'MagentoInvoice']),
            ]

    def get_migration(self):
        environ.add_resource('magentosql', os.path.join(plugin_root, 'sql'))
        return PluginSchemaMigration(self.name, 'magentosql',
                                     ['*.sql', '*.py'])

    #
    #  Private
    #

    @inlineCallbacks
    def _synchronize_magento_table(self, mag_table):
        log.info("Start synchronizing %s" % mag_table)
        retval = yield mag_table.synchronize()
        log.info("Finish synchronizing magento table %s with status: %s"
                 % (mag_table, retval))
        returnValue(retval)

    def _get_magento_product_by_product(self, product):
        conn = product.get_connection()
        mag_product = MagentoProduct.selectOneBy(connection=conn,
                                                 product=product)
        assert mag_product
        return mag_product

    def _get_magento_sale_by_sale(self, sale):
        conn = sale.get_connection()
        mag_sale = MagentoSale.selectOneBy(connection=conn,
                                           sale=sale)
        assert mag_sale
        return mag_sale

    #
    #  Callbacks
    #

    def _on_product_create(self, product, **kwargs):
        # Just create the registry and it will be synchronized later.
        MagentoProduct(connection=product.get_connection(),
                       product=product)

    def _on_product_update(self, product, **kwargs):
        mag_product = self._get_magento_product_by_product(product)
        mag_product.need_sync = True

    def _on_product_delete(self, product, **kwargs):
        mag_product = self._get_magento_product_by_product(product)
        # Remove the foreign key reference, so the product can be
        # deleted on stoq without problems. This deletion will happen
        # later when synchronizing products.
        mag_product.product = None
        mag_product.need_sync = True

    def _on_product_stock_update(self, product, branch, old_quantity,
                                 new_quantity, **kwargs):
        conn = product.get_connection()
        mag_product = self._get_magento_product_by_product(product)

        mag_stock = MagentoStock.selectOneBy(connection=conn,
                                             magento_product=mag_product)
        # Maybe we do not have mag_stock yet. It's created on MagentoProduct
        # create method. There's no problem because, when it gets created, it's
        # need_sync attribute will be True by default.
        if mag_stock:
            mag_stock.need_sync = True

    def _on_sale_status_change(self, sale, old_status, **kwargs):
        mag_sale = self._get_magento_sale_by_sale(sale)
        mag_sale.need_sync = True


register_plugin(MagentoPlugin)
