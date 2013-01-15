# -*- coding: utf-8 -*-

from domain.magentoproduct import MagentoProduct, MagentoCategory


def apply_patch(store):
    # Add 'status' to magento_product
    store.execute("""
        ALTER TABLE magento_product
            ADD COLUMN status integer DEFAULT %s;
        """ % MagentoProduct.STATUS_NONE)

    # Add 'description', and 'meta_keywords' to magento_category.
    # Also, remove 'parent_id' from it.
    store.execute("""
        ALTER TABLE magento_category
            ADD COLUMN description text;
        ALTER TABLE magento_category
            ADD COLUMN meta_keywords text;
        ALTER TABLE magento_category
            DROP COLUMN parent_id;
        """)

    for mag_category in store.find(MagentoCategory):
        mag_category.is_active = None if mag_category.parent else True
        mag_category.need_sync = True

    # Mark all magento_category as needing sync
    store.execute("UPDATE magento_category SET need_sync = 'TRUE';")
