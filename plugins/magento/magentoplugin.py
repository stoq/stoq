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

import datetime
import os
import sys
import time

from kiwi.environ import environ
from kiwi.log import Logger
from twisted.internet import reactor
from twisted.internet.defer import (DeferredLock, returnValue, inlineCallbacks,
                                    gatherResults)
from twisted.internet.task import LoopingCall
from zope.interface import implements

from stoqlib.database.migration import PluginSchemaMigration
from stoqlib.database.runtime import get_connection
from stoqlib.domain.events import (ProductCreateEvent, ProductRemoveEvent,
                                   ProductEditEvent, ProductStockUpdateEvent,
                                   CategoryCreateEvent, CategoryEditEvent,
                                   SaleStatusChangedEvent)
from stoqlib.lib.interfaces import IPlugin
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.pluginmanager import register_plugin

plugin_root = os.path.dirname(__file__)
sys.path.append(plugin_root)
from domain.magentoconfig import MagentoConfig
from domain.magentoclient import MagentoClient, MagentoAddress
from domain.magentoproduct import (MagentoProduct, MagentoStock, MagentoImage,
                                   MagentoCategory)
from domain.magentosale import MagentoSale, MagentoInvoice, MagentoShipment
from magentoui import MagentoUI

_ = stoqlib_gettext
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
            for table in (MagentoProduct, MagentoStock, MagentoCategory,
                          MagentoImage, MagentoClient, MagentoAddress,
                          MagentoSale, MagentoInvoice, MagentoShipment):
                # Use gatherResults to allow multiple servers to be
                # synchronized at the same time. Can save a lot of time!
                retval = yield gatherResults(
                    [self._synchronize_magento_table(table, config) for config
                     in MagentoConfig.select(connection=get_connection())]
                    )
                retval_list.append(all(retval))
            returnValue(all(retval_list))
        finally:
            self._lock.release()

    #
    #  IPlugin implementation
    #

    def activate(self):
        environ.add_resource('glade', os.path.join(plugin_root, 'glade'))
        self.ui = MagentoUI()

        # Connect product events
        ProductCreateEvent.connect(self._on_product_create)
        ProductRemoveEvent.connect(self._on_product_delete)
        ProductEditEvent.connect(self._on_product_update)
        ProductStockUpdateEvent.connect(self._on_product_stock_update)

        # Connect category events
        CategoryCreateEvent.connect(self._on_category_create)
        CategoryEditEvent.connect(self._on_category_update)

        # Connect sale events
        SaleStatusChangedEvent.connect(self._on_sale_status_change)

    def get_tables(self):
        return [
            ('domain.magentoconfig', ['MagentoConfig',
                                      'MagentoTableDict',
                                      'MagentoTableDictItem'])
            ('domain.magentoproduct', ['MagentoProduct',
                                       'MagentoStock',
                                       'MagentoCategory',
                                       'MagentoImage']),
            ('domain.magentoclient', ['MagentoClient',
                                      'MagentoAddress']),
            ('domain.magentosale', ['MagentoSale',
                                    'MagentoInvoice']),
            ]

    def get_migration(self):
        environ.add_resource('magentosql', os.path.join(plugin_root, 'sql'))
        return PluginSchemaMigration(self.name, 'magentosql', ['*.sql'])

    def get_dbadmin_commands(self):
        return ['sync']

    def handle_dbadmin_command(self, command, options, args):
        mag_cmd = _MagentoCmd(self)
        if command == 'sync':
            try:
                mag_cmd.start_sync()
            except KeyboardInterrupt:
                mag_cmd.stop_sync()
        else:
            raise KeyError(_("Invalid command given"))

    #
    #  Private
    #

    @inlineCallbacks
    def _synchronize_magento_table(self, mag_table, config):
        url = config.url

        log.info("Start synchronizing %s on server %s" % (mag_table, url))
        retval = yield mag_table.synchronize(config)
        log.info("Start synchronizing %s on server %s with retval %s" %
                 (mag_table, url, retval))

        returnValue(retval)

    def _get_magento_products_by_product(self, product):
        conn = product.get_connection()
        mag_products = MagentoProduct.selectBy(connection=conn,
                                               product=product)
        return mag_products

    def _get_magento_categories_by_category(self, category):
        conn = category.get_connection()
        mag_categories = MagentoCategory.selectBy(connection=conn,
                                                  category=category)
        return mag_categories

    #
    #  Callbacks
    #

    def _on_product_create(self, product, **kwargs):
        conn = product.get_connection()
        for config in MagentoConfig.select(connection=conn):
            # Just create the registry and it will be synchronized later.
            MagentoProduct(connection=conn,
                           product=product,
                           config=config)

    def _on_product_update(self, product, **kwargs):
        for mag_product in self._get_magento_products_by_product(product):
            mag_product.need_sync = True

    def _on_product_delete(self, product, **kwargs):
        for mag_product in self._get_magento_products_by_product(product):
            # Remove the foreign key reference, so the product can be
            # deleted on stoq without problems. This deletion will happen
            # later when synchronizing products.
            mag_product.product = None
            mag_product.need_sync = True

    def _on_product_stock_update(self, product, branch, old_quantity,
                                 new_quantity, **kwargs):
        conn = product.get_connection()
        for mag_product in self._get_magento_products_by_product(product):
            for mag_stock in MagentoStock.selectBy(connection=conn,
                                                   magento_product=mag_product):
                mag_stock.need_sync = True

    def _on_category_create(self, category, **kwargs):
        conn = category.get_connection()
        for config in MagentoConfig.select(connection=conn):
            # Just create the registry and it will be synchronized later.
            MagentoCategory(connection=conn,
                            category=category,
                            config=config)

    def _on_category_update(self, category, **kwargs):
        for mag_category in self._get_magento_categories_by_category(category):
            mag_category.need_sync = True

    def _on_sale_status_change(self, sale, old_status, **kwargs):
        mag_sale = MagentoSale.selectOneBy(connection=sale.get_connection(),
                                           sale=sale)
        if mag_sale:
            mag_sale.need_sync = True


register_plugin(MagentoPlugin)


class _MagentoCmd(object):
    """Sync daemon for magento

    @cvar SYNC_INTERVAL: the interval between looping calls, in sec
    @cvar CMDS: available commands for dbadmin
    """

    SYNC_INTERVAL = 15

    def __init__(self, plugin):
        self._plugin = plugin

    #
    #  Public API
    #

    def start_sync(self):
        lc = LoopingCall(self._sync)
        lc.start(self.SYNC_INTERVAL)
        reactor.run()

    def stop_sync(self):
        if reactor.running:
            reactor.stop()

    #
    #  Private
    #

    @inlineCallbacks
    def _sync(self):
        t_before = time.time()
        print _("Magento synchronization initialized..")

        try:
            retval = yield self._plugin.synchronize()
        except Exception:
            # We don't want the daemon to stop! If there's an error, we
            # will indicate it on stdout and log the problem
            retval = False
            log.err()

        t_after = time.time()
        t_delta = datetime.timedelta(seconds=-int(t_before - t_after))
        status = _("OK") if retval else _("With errors")

        # Simple stdout feedback
        print _("Magento synchronization finished:")
        print _("    Status: %s") % (status,)
        print _("    Time took: %s") % (t_delta,)
