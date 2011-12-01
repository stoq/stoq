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

import base64
import datetime
import urllib

from dateutil.relativedelta import relativedelta
from kiwi.log import Logger
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.xmlrpc import Fault

from stoqlib.database.orm import (IntCol, UnicodeCol, DateTimeCol, BLOBCol,
                                  BoolCol, ForeignKey, SingleJoin,
                                  MultipleJoin, IN)
from stoqlib.database.runtime import get_connection
from stoqlib.domain.interfaces import IStorable

from domain.magentobase import MagentoBaseSyncUp
from magentolib import get_proxy

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

    sku = UnicodeCol(default=None)
    product_type = UnicodeCol(default=TYPE_SIMPLE)
    product_set = IntCol(default=None)
    visibility = IntCol(default=VISIBILITY_CATALOG_SEARCH)
    url_key = UnicodeCol(default=None)
    news_from_date = DateTimeCol(default=None)
    news_to_date = DateTimeCol(default=None)
    magento_category = ForeignKey('MagentoCategory', default=None)
    product = ForeignKey('Product')

    magento_stock = SingleJoin('MagentoStock',
                               joinColumn='magento_product_id')
    magento_images = MultipleJoin('MagentoImage',
                                  joinColumn='magento_product_id')

    #
    #  MagentoBase hooks
    #

    @classmethod
    @inlineCallbacks
    def ensure_config(cls, config):
        # Ensure we know the id of the default set
        if not config.default_product_set:
            proxy = get_proxy(config)
            try:
                set_list = yield proxy.call('product_attribute_set.list')
            except Fault as err:
                log.warning("An error occurried when trying to get the "
                            "default product set on magento: %s"
                            % err.faultString)
                returnValue(False)

            default_set = None
            for set_ in set_list:
                if set_['name'] == 'Default':
                    default_set = set_['set_id']
                    break
            if not default_set:
                returnValue(False)
            config.default_product_set = default_set

        returnValue(True)

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
                retval = yield MagentoProduct.info_remote(self.config,
                                                          self.sku)
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
                         config=self.config,
                         magento_product=self)
            image = self.product.full_image
            if image:
                self._update_main_image(image)
            category = self.product.sellable.category
            if category:
                self._update_category(category)

        returnValue(bool(retval))

    @inlineCallbacks
    def update_remote(self):
        # If no product, that means we need to remove it from magento
        if not self.product:
            retval = yield self.remove_remote()
            returnValue(retval)

        image = self.product.full_image
        if image:
            self._update_main_image(image)
        category = self.product.sellable.category
        if category:
            self._update_category(category)

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
        for mag_image in self.magento_images:
            mag_image.delete(mag_image.id, conn)
        self.delete(self.id, conn)

        returnValue(retval)

    #
    #  Private
    #

    def _update_category(self, category):
        conn = self.get_connection()
        mag_category = self.magento_category

        if mag_category and mag_category.category == category:
            # Nothing changed..return here to skip processing bellow
            return
        elif mag_category and mag_category.category != category:
            # Make sure we will remove the product from the category
            mag_category.need_sync = True

        mag_category = MagentoCategory.selectOneBy(connection=conn,
                                                   config=self.config,
                                                   category=category)
        self.magento_category = mag_category
        self.magento_category.need_sync = True

    def _update_main_image(self, image):
        conn = self.get_connection()
        mag_image = MagentoImage.selectOneBy(connection=conn,
                                             magento_product=self,
                                             is_main=True)

        if mag_image and mag_image.image == image:
            # Nothing changed..return here to skip processing bellow
            return
        elif mag_image and mag_image.image != image:
            # This won't be the main image anymore.
            mag_image.is_main = False

        label = self.product.sellable.get_description()
        mag_image = MagentoImage(connection=conn,
                                 magento_id=self.magento_id,
                                 config=self.config,
                                 image=image,
                                 is_main=True,
                                 label=label,
                                 magento_product=self)

    def _generate_initial_data(self):
        sellable = self.product.sellable
        config = self.config

        if not self.product_set:
            self.product_set = config.default_product_set
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
    def list_remote(cls, config, *args, **kwargs):
        args = list(args)
        if not args:
            # If this is not an info call, mimic the list api behavior
            args.append([mag_stock.magento_id for mag_stock in
                         cls.selectBy(connection=get_connection(),
                                      config=config)])

        retval = yield super(MagentoStock, cls).list_remote(config, *args,
                                                            **kwargs)
        returnValue(retval)

    @classmethod
    @inlineCallbacks
    def info_remote(cls, config, id, *args):
        # Mimic info api as stock doesn't have one
        retval = yield cls.list_remote(config, [id])
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


class MagentoImage(MagentoBaseSyncUp):
    """Class for product image synchronization between Stoq and Magento"""

    API_NAME = 'product_media'
    API_ID_NAME = MagentoProduct.API_ID_NAME

    (ERROR_IMAGE_STORE_VIEW_NOT_FOUND,
     ERROR_IMAGE_PRODUCT_NOT_EXISTS,
     ERROR_IMAGE_PRODUCT_INVALID_DATA,
     ERROR_IMAGE_NOT_EXISTS,
     ERROR_IMAGE_CREATION_FAILED,
     ERROR_IMAGE_NOT_UPDATED,
     ERROR_IMAGE_NOT_REMOVED,
     ERROR_IMAGE_NO_SUPPORT) = range(100, 108)

    TYPE_BASE_IMAGE = 'image'
    TYPE_SMALL_IMAGE = 'small_image'
    TYPE_THUMBNAIL = 'thumbnail'

    image = BLOBCol()
    filename = UnicodeCol(default=None)
    is_main = BoolCol(default=False)
    label = UnicodeCol(default=None)
    visible = BoolCol(default=True)
    magento_product = ForeignKey('MagentoProduct')

    #
    #  MagentoBaseSyncUp hooks
    #

    def need_create_remote(self):
        # When we create an image, it doesn't return an id, but a filename
        if not self.filename:
            return True

        return super(MagentoImage, self).need_create_remote()

    @inlineCallbacks
    def create_remote(self):
        image_data = self._get_data()
        image_data.update({
            'file': {
                'name': urllib.quote('%s%s' % (self.label, self.id)),
                'content': base64.b64encode(self.image),
                # All of our images are stored as png
                'mime': 'image/png',
                }
            })
        data = [self.magento_product.magento_id, image_data]

        try:
            retval = yield self.proxy.call('product_media.create', data)
        except Fault as err:
            log.warning("An error occurried when trying to create a product's "
                        "image on magento: %s" % err.faultString)
            returnValue(False)
        else:
            self.filename = retval

        returnValue(bool(retval))

    @inlineCallbacks
    def update_remote(self):
        image_data = self._get_data()
        data = [self.magento_product.magento_id, self.filename, image_data]

        try:
            retval = yield self.proxy.call('product_media.update', data)
        except Fault as err:
            log.warning("An error occurried when trying to update a product's "
                        "image on magento: %s" % err.faultString)
            returnValue(False)

        returnValue(retval)

    #
    #  Private
    #

    def _get_data(self):
        types = []
        if self.is_main:
            types.extend([self.TYPE_BASE_IMAGE, self.TYPE_SMALL_IMAGE,
                          self.TYPE_THUMBNAIL])

        return {
            'types': types,
            'label': self.label,
            'exclude': not self.visible,
            }


class MagentoCategory(MagentoBaseSyncUp):
    """Class for product category synchronization between Stoq and Magento"""

    API_NAME = 'category'
    API_ID_NAME = 'category_id'

    (ERROR_CATEGORY_STORE_VIEW_NOT_FOUND,
     ERROR_CATEGORY_WEBSITE_NOT_EXISTS,
     ERROR_CATEGORY_NOT_EXISTS,
     ERROR_CATEGORY_INVALID_DATA,
     ERROR_CATEGORY_NOT_MOVED,
     ERROR_CATEGORY_NOT_DELETED,
     ERROR_CATEGORY_PRODUCT_NOT_ASSIGNED) = range(100, 107)

    is_active = BoolCol(default=True)
    category = ForeignKey('SellableCategory')
    parent = ForeignKey('MagentoCategory', default=None)

    magento_products = MultipleJoin('MagentoProduct',
                                    joinColumn='magento_category_id')

    #
    #  Classmethods
    #

    @classmethod
    @inlineCallbacks
    def tree_remote(cls, config, parent_id=None):
        data = []
        if parent_id:
            data.append(parent_id)

        proxy = get_proxy(config)
        try:
            retval = yield proxy.call('category.tree', data)
        except Fault as err:
            log.warning("An error occurried when trying get a categories tree "
                        "on magento: %s" % err.faultString)
            returnValue(False)

        returnValue(retval)

    #
    #  Public API
    #

    @inlineCallbacks
    def assigned_products_remote(self):
        try:
            retval = yield self.proxy.call('category.assignedProducts',
                                           [self.magento_id])
        except Fault as err:
            log.warning("An error occurried when trying get a category "
                        "assigned product list on magento: %s"
                        % err.faultString)
            returnValue(False)

        returnValue(retval)

    @inlineCallbacks
    def assign_product_remote(self, magento_product):
        data = [self.magento_id, magento_product.magento_id]

        try:
            retval = yield self.proxy.call('category.assignProduct', data)
        except Fault as err:
            log.warning("An error occurried when trying assign a product "
                        "to a category on magento: %s" % err.faultString)
            returnValue(False)

        returnValue(retval)

    @inlineCallbacks
    def remove_product_remote(self, magento_product):
        data = [self.magento_id, magento_product.magento_id]

        try:
            retval = yield self.proxy.call('category.removeProduct', data)
        except Fault as err:
            if err.faultCode == self.ERROR_CATEGORY_PRODUCT_NOT_ASSIGNED:
                # The product isn't assigned. That's what we wanted
                returnValue(True)

            log.warning("An error occurried when trying assign a product "
                        "to a category on magento: %s" % err.faultString)
            returnValue(False)

        returnValue(retval)

    #
    #  MagentoBase hooks
    #

    @classmethod
    @inlineCallbacks
    def ensure_config(cls, config):
        # Ensure we know the root category
        if not config.root_category:
            tree = yield cls.tree_remote(config)
            if not tree:
                returnValue(False)

            # The root will be the dict retrieved by tree
            root_category = tree[cls.API_ID_NAME]
            if not root_category:
                returnValue(False)
            config.root_category = root_category

        returnValue(True)

    #
    #  MagentoBaseSyncUp hooks
    #

    @inlineCallbacks
    def create_remote(self):
        if self.parent:
            parent_id = self.parent.magento_id
        else:
            parent_id = self.config.root_category

        data = [parent_id, self._get_data()]
        try:
            retval = yield self.proxy.call('category.create', data)
        except Fault as err:
            log.warning("An error occurried when trying to create a category "
                        "on magento: %s" % err.faultString)
            returnValue(False)
        else:
            self.magento_id = retval
            # Ensure we will call update to assign products properly.
            # We don't do it here because, if it fails, we will try to create
            # the category on magento again, resulting in an error.
            self.keep_need_sync = True

        returnValue(bool(retval))

    @inlineCallbacks
    def update_remote(self):
        conn = self.get_connection()
        data = [self.magento_id, self._get_data()]

        try:
            retval = yield self.proxy.call('category.update', data)
        except Fault as err:
            log.warning("An error occurried when trying to update a category "
                        "on magento: %s" % err.faultString)
            returnValue(False)

        assigned_products = yield self.assigned_products_remote()
        # Find what products miss assignment for self and assign
        if not assigned_products in (None, False):
            retval_list = []
            assigned_ids = [ap[MagentoProduct.API_ID_NAME] for ap
                            in assigned_products]

            for mag_product in self.magento_products:
                if mag_product.magento_id in assigned_ids:
                    # Remove the id from the list, to allow us to find the ones
                    # that we need to remove bellow.
                    assigned_ids.remove(mag_product.magento_id)
                    continue

                retval_ = yield self.assign_product_remote(mag_product)
                retval_list.append(retval_)
            # Deassign products not listed on self anymore
            if assigned_ids:
                for mag_product in MagentoProduct.select(
                    connection=conn,
                    clause=IN(MagentoProduct.q.magento_id, assigned_ids),
                    ):
                    retval_ = yield self.remove_product_remote(mag_product)
                    retval_list.append(retval_)

            retval = retval and all(retval_list)

        returnValue(retval)

    #
    #  Private
    #

    def _get_data(self):
        name = self.category.get_description()
        # Base categories are not visible.
        include_in_menu = bool(self.category.category)

        available_sort_by = ['name', 'price']
        default_sort_by = available_sort_by[0]

        return {
            'name': name,
            'is_active': self.is_active,
            'include_in_menu': include_in_menu,
            'available_sort_by': available_sort_by,
            'default_sort_by': default_sort_by,
            }
