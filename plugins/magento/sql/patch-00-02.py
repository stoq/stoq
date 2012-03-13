# -*- coding: utf-8 -*-

from domain.magentoproduct import MagentoImage


def apply_patch(trans):
    # Remove 'image' and 'label' colum from magento_image
    # Also, add 'image_id' foreing key to magento_image
    trans.query("""
          ALTER TABLE magento_image
              DROP COLUMN label;
          ALTER TABLE magento_image
              DROP COLUMN image;
          ALTER TABLE magento_image
              ADD COLUMN image_id bigint REFERENCES image(id);
          """)

    # Migrate MagentoImage to Image
    for mag_image in MagentoImage.select(connection=trans):
        sellable = mag_image.magento_product.product.sellable
        image = sellable.image

        if not image.description:
            image.description = '%s #%s' % (sellable.get_description(),
                                            sellable.id)

        mag_image.image = image
        mag_image.need_sync = True

    # Add 'magento_address_id' foreing key to magento_sale
    trans.query("""
          ALTER TABLE magento_sale
              ADD COLUMN magento_address_id bigint REFERENCES magento_address(id);
          """)

    # Add 'delivery_id' foreing key to delivery
    trans.query("""
          ALTER TABLE magento_shipment
              ADD COLUMN delivery_id bigint REFERENCES delivery(id);
          """)
