# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
from twisted.internet.defer import inlineCallbacks, returnValue

from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.product import Product
from stoqlib.domain.sellable import Sellable

from domain.magentoproduct import MagentoProduct, MagentoStock

log = Logger('plugins.magento.domain.magentoproduct')


@inlineCallbacks
def import_products(config):
    """Import products from Magento

    @returns: C{True} if all products imported sucessful, C{False}
        otherwise
    """
    # FIXME: This should be in a subclass of stoqlib.importer.Importer
    retval = True
    trans = new_transaction()

    filters = {
        # Exclude already imported products
        MagentoProduct.API_ID_NAME: {
            'nin': [mag_p.magento_id for mag_p in
                    MagentoProduct.select(connection=trans, config=config)]},
        # Stoq only supports simple products right now
        'type': {'eq': MagentoProduct.TYPE_SIMPLE},
        }
    product_list = yield MagentoProduct.list_remote(config, **filters)
    # Empty lists are fine! That means we don't have anything to import
    if product_list in (None, False):
        returnValue(False)

    for magento_id in [p[MagentoProduct.API_ID_NAME] for p in product_list]:
        product_info = yield MagentoProduct.info_remote(config, magento_id)
        stock_info = yield MagentoStock.info_remote(config, magento_id)
        if not product_info or not stock_info:
            finish_transaction(trans, False)
            retval = False
            break

        sellable = Sellable(
            connection=trans,
            description=product_info['name'],
            # FIXME: Cost isn't visible on info
            #cost=product_info['cost'],
            price=product_info['price'],
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
        elif product_info['status'] == MagentoProduct.STATUS_DISABLED:
            sellable.close()

        mag_product = MagentoProduct(
            connection=trans,
            config=config,
            magento_id=magento_id,
            sku=product_info['sku'],
            product_type=product_info['type'],
            product_set=product_info['set'],
            visibility=product_info['visibility'],
            url_key=product_info['url_key'],
            news_from_date=product_info['news_from_date'],
            news_to_date=product_info['news_to_date'],
            product=product,
            )
        MagentoStock(
            connection=trans,
            config=config,
            magento_id=magento_id,
            magento_product=mag_product,
            )

        finish_transaction(trans, True)

    trans.close()
    returnValue(retval)
