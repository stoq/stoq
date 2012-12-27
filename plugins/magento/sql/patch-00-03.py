# -*- coding: utf-8 -*-

from domain.magentoproduct import MagentoProduct
from stoqlib.domain.product import Product


def apply_patch(store):
    # Add 'sellable_id' foreing key to magento_product
    store.execute("""
          ALTER TABLE magento_product
              ADD COLUMN sellable_id bigint REFERENCES sellable(id);
          """)

    mag_product_list = store.execute("SELECT id, product_id "
                                      "    FROM magento_product;").get_all()
    if mag_product_list:
        for id, product_id in mag_product_list:
            if product_id:
                product = Product.get(product_id, store)
                mag_product = MagentoProduct.get(id, store)
                mag_product.sellable = product.sellable

    # Drop 'product_id' column from magento_product
    store.execute("""
          ALTER TABLE magento_product
              DROP COLUMN product_id;
          """)

    # Add 'can_deliver' magento_sale
    store.execute("""
          ALTER TABLE magento_sale
              ADD COLUMN can_deliver boolean;
          """)
