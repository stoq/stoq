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

import datetime
import urllib

from dateutil.relativedelta import relativedelta
from kiwi.log import Logger
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.xmlrpc import Fault

from stoqlib.database.orm import (IntCol, UnicodeCol, DateTimeCol, ForeignKey,
                                  SingleJoin)
from stoqlib.database.runtime import (get_connection, new_transaction,
                                      finish_transaction)
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.product import Product
from stoqlib.domain.sellable import BaseSellableInfo, Sellable

from domain.magentobase import MagentoBaseSyncUp
from domain.magentoconfig import get_config

log = Logger('plugins.magento.domain.magentoproduct')


class MagentoProduct(MagentoBaseSyncUp):
    """Class for products synchronization between Stoq and Magento"""

    API_NAME = 'product'
    API_ID_NAME = 'product_id'

    ERROR_PRODUCT_ALREADY_EXISTS = 1
    (ERROR_PRODUCT_STORE_VIEW_NOT_FOUND,
     ERROR_PRODUCT_NOT_EXISTS,
     ERROR_PRODUCT_INVALID_DATA,
     ERROR_PRODUCT_NOT_DELETED) = range(100, 104)

    (STATUS_NONE,
     STATUS_ENABLED,
     STATUS_DISABLED) = range(3)

    (VISIBILITY_NONE,
     VISIBILITY_NOT_INDIVIDUALLY,
     VISIBILITY_CATALOG,
     VISIBILITY_SEARCH,
     VISIBILITY_CATALOG_SEARCH) = range(5)

    TYPE_SIMPLE = 'simple'
    TYPE_GROUPED = 'grouped'
    TYPE_CONFIGURABLE = 'configurable'
    TYPE_VIRTUAL = 'virtual'
    TYPE_BUNDLE = 'bundle'
    TYPE_DOWNLOADABLE = 'downloadable'

    TAX_NONE = 0
    TAX_TAXABLE_GOODS = 2
    TAX_SHIPPING = 4

    DEFAULT_SET = 4

    sku = UnicodeCol(default=None)
    product_type = UnicodeCol(default=TYPE_SIMPLE)
    product_set = IntCol(default=DEFAULT_SET)
    visibility = IntCol(default=VISIBILITY_CATALOG_SEARCH)
    url_key = UnicodeCol(default=None)
    news_from_date = DateTimeCol(default=None)
    news_to_date = DateTimeCol(default=None)
    product = ForeignKey('Product')

    magento_stock = SingleJoin('MagentoStock',
                               joinColumn='magento_product_id')

    #
    #  Classmethods
    #

    @classmethod
    @inlineCallbacks
    def import_from_magento(cls):
        """Import products from Magento

        @returns: C{True} if all products imported sucessful,
            C{False} otherwise
        """
        retval = True
        trans = new_transaction()
        config = get_config(trans)

        filters = {
            # Exclude already imported products
            cls.API_ID_NAME: {'nin': [mag_p.magento_id for mag_p in
                                      cls.select(connection=trans)]},
            # Stoq only supports simple products with default set right now
            'type': {'eq': cls.TYPE_SIMPLE},
            'set': {'eq': cls.DEFAULT_SET},
            }
        product_list = yield cls.list_remote(**filters)
        # Empty lists are fine! That means we don't have anything to import
        if product_list in (None, False):
            returnValue(False)

        for magento_id in [p[cls.API_ID_NAME] for p in product_list]:
            product_info = yield cls.info_remote(magento_id)
            stock_info = yield MagentoStock.info_remote(magento_id)
            if not product_info or not stock_info:
                finish_transaction(trans, False)
                retval = False
                break

            base_sellable_info = BaseSellableInfo(
                connection=trans,
                description=product_info['name'],
                # FIXME: Cost isn't visible on info
                #cost=product_info['cost'],
                price=product_info['price'],
                )
            sellable = Sellable(
                connection=trans,
                base_sellable_info=base_sellable_info,
                notes=product_info['description'],
                )
            product = Product(
                connection=trans,
                sellable=sellable,
                weight=product_info['weight'],
                )

            storable = product.addFacet(IStorable, connection=trans)
            # FIXME: If there's stock on Magento, but product status is
            #        disabled, how to indicate that on Stoq? (we can only close
            #        products that does not have any stock available)
            if stock_info['qty']:
                storable.increase_stock(stock_info['qty'], config.branch)
            elif product_info['status'] == cls.STATUS_DISABLED:
                sellable.close()

            mag_product = cls(connection=trans,
                              magento_id=magento_id,
                              sku=product_info['sku'],
                              product_type=product_info['type'],
                              product_set=product_info['set'],
                              visibility=product_info['visibility'],
                              url_key=product_info['url_key'],
                              news_from_date=product_info['news_from_date'],
                              news_to_date=product_info['news_to_date'],
                              product=product)
            MagentoStock(connection=trans,
                         magento_id=magento_id,
                         magento_product=mag_product)

            finish_transaction(trans, True)

        trans.close()
        returnValue(retval)

    #
    #  MagentoBaseSyncUp hooks
    #

    @inlineCallbacks
    def create_remote(self):
        assert not self.magento_id

        # If no product, that means we need to remove it from magento.
        # Can happen if one creates a product and deletes it, before we could
        # sync self and create it on Magento.
        if not self.product:
            retval = yield self.remove_remote()
            returnValue(retval)

        self._generate_initial_data()
        data = [self.product_type, self.product_set, self.sku,
                self._get_data()]
        try:
            retval = yield self.proxy.call('product.create', data)
        except Fault as err:
            if err.faultCode == self.ERROR_PRODUCT_ALREADY_EXISTS:
                # If product exists, get its id and update it
                retval = yield MagentoProduct.info_remote(self.sku)
                if retval:
                    self.magento_id = retval[self.API_ID_NAME]
            else:
                log.warning("An error occurried when trying to create a "
                            "product on magento: %s" % err.faultString)
                returnValue(False)
        else:
            self.magento_id = retval

        if retval:
            MagentoStock(connection=self.get_connection(),
                         magento_id=self.magento_id,
                         magento_product=self)
            retval = yield self.update_remote()

        returnValue(bool(retval))

    @inlineCallbacks
    def update_remote(self):
        # If no product, that means we need to remove it from magento
        if not self.product:
            retval = yield self.remove_remote()
            returnValue(retval)

        data = [self.magento_id, self._get_data()]
        try:
            retval = yield self.proxy.call('product.update', data)
        except Fault as err:
            log.warning("An error occurried when trying to update a product "
                        "on magento: %s" % err.faultString)
            returnValue(False)

        returnValue(retval)

    @inlineCallbacks
    def remove_remote(self):
        try:
            retval = yield self.proxy.call('product.delete', [self.magento_id])
        except Fault as err:
            if err.faultCode == self.ERROR_PRODUCT_NOT_EXISTS:
                # The product was already deleted on magento.
                # That's what we wanted!
                retval = True
            else:
                log.warning("An error occurried when trying to delete a "
                            "product on magento: %s" % err.faultString)
                returnValue(False)

        conn = self.get_connection()
        mag_stock = self.magento_stock
        if mag_stock:
            mag_stock.delete(mag_stock.id, conn)
        self.delete(self.id, conn)

        returnValue(retval)

    #
    #  Private
    #

    def _generate_initial_data(self):
        sellable = self.product.sellable
        config = self.config

        if not self.sku:
            # SKU is a product identifier on Magento and must be unique
            self.sku = 'SK%s' % str(sellable.id).zfill(20)
        if not self.news_from_date:
            self.news_from_date = datetime.datetime.now()
        if not self.news_to_date:
            self.news_to_date = (self.news_from_date +
                                 relativedelta(days=config.qty_days_as_new))
        if not self.url_key:
            self.url_key = urllib.quote_plus(str(sellable.get_description()))

    def _get_data(self):
        sellable = self.product.sellable
        status = (self.STATUS_DISABLED if sellable.is_closed() else
                  self.STATUS_ENABLED)
        tax_class_id = (self.TAX_TAXABLE_GOODS if sellable.tax_constant else
                        self.TAX_NONE)

        return {
            'status': status,
            'name': sellable.get_description(),
            'description': sellable.notes,
            'short_description': sellable.notes.split('\n')[0],
            'cost': sellable.cost,
            'price': sellable.price,
            'tax_class_id': tax_class_id,
            'url_key': self.url_key,
            'news_from_date': self.news_from_date,
            'news_to_date': self.news_to_date,
            'visibility': self.visibility,
            'weight': self.product.weight or 1,
            }


class MagentoStock(MagentoBaseSyncUp):
    """Class for product stock synchronization between Stoq and Magento"""

    API_NAME = 'product_stock'
    API_ID_NAME = MagentoProduct.API_ID_NAME

    (ERROR_STOCK_PRODUCT_NOT_EXISTS,
     ERROR_STOCK_NOT_UPDATED) = range(101, 103)

    magento_product = ForeignKey('MagentoProduct')

    #
    #  MagentoBase hooks
    #

    @classmethod
    @inlineCallbacks
    def list_remote(cls, *args, **kwargs):
        args = list(args)
        if not args:
            # If this is not an info call, mimic the list api behavior
            args.append([mag_stock.magento_id for mag_stock in
                         cls.select(connection=get_connection())])

        retval = yield super(MagentoStock, cls).list_remote(*args, **kwargs)
        returnValue(retval)

    @classmethod
    @inlineCallbacks
    def info_remote(cls, id, *args):
        # Mimic info api as stock doesn't have one
        retval = yield cls.list_remote([id])
        returnValue(retval and retval[0])

    #
    #  MagentoBaseSyncUp hooks
    #

    @inlineCallbacks
    def update_remote(self):
        data = [self.magento_id, self._get_data()]
        try:
            retval = yield self.proxy.call('product_stock.update', data)
        except Fault as err:
            log.warning("An error occurried when trying to update a product's "
                        "stock on magento: %s" % err.faultString)
            returnValue(False)

        returnValue(retval)

    #
    #  Private
    #

    def _get_data(self):
        quantity = 0
        product = self.magento_product.product
        storable = IStorable(product, None)

        if storable:
            # Get stock items from branch on config
            branch = self.config.branch
            stock_item = storable.get_stock_item(branch)
            if stock_item:
                quantity = stock_item.quantity + stock_item.logic_quantity

        return {
            'qty': quantity,
            'is_in_stock': int(product.sellable.can_be_sold()),
            }
