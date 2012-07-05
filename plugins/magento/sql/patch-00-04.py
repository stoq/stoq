# -*- coding: utf-8 -*-

from domain.magentoproduct import MagentoProduct, MagentoCategory


def apply_patch(trans):
    # Add 'status' to magento_product
    trans.query("""
        ALTER TABLE magento_product
            ADD COLUMN status integer DEFAULT %s;
        """ % MagentoProduct.STATUS_NONE)

    # Add 'description', and 'meta_keywords' to magento_category.
    # Also, remove 'parent_id' from it.
    trans.query("""
        ALTER TABLE magento_category
            ADD COLUMN description text;
        ALTER TABLE magento_category
            ADD COLUMN meta_keywords text;
        ALTER TABLE magento_category
            DROP COLUMN parent_id;
        """)

    for mag_category in MagentoCategory.select(connection=trans):
        mag_category.is_active = None if mag_category.parent else True
        mag_category.need_sync = True

    # Mark all magento_category as needing sync
    trans.query("UPDATE magento_category SET need_sync = 'TRUE';")
