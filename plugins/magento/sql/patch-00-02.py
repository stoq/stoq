# -*- coding: utf-8 -*-

# Ensure we have a MagentoProduct for all existing Products.
# We are doing this on a patch because other will be created by events

from stoqlib.domain.product import Product

from domain.magentoproduct import MagentoProduct


def apply_patch(trans):
    for product in Product.select(connection=trans):
        if not MagentoProduct.selectOneBy(connection=trans,
                                          product=product):
            # Just need to create. All other information will be synchronized
            # on MagentoProduct.synchronize
            mag_product = MagentoProduct(connection=trans,
                                         product=product)
            assert mag_product
