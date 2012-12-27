import StringIO

from PIL import Image as PIL_Image
from stoqlib.domain.image import Image
from stoqlib.domain.product import Product
from stoqlib.domain.service import Service
from stoqlib.lib.parameters import sysparam


def apply_patch(store):
    # Create tables for Image and a reference on Product and Service
    store.execute("""
          CREATE TABLE image (
              id serial NOT NULL PRIMARY KEY,
              te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
              te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

              image bytea,
              thumbnail bytea,
              description text
          );

          ALTER TABLE sellable
              ADD COLUMN image_id bigint UNIQUE REFERENCES image(id);
          """)

    # Migrate all Product images to Image
    product_image_list = store.execute("""
                   SELECT id FROM product WHERE image != '';""").get_all()

    if product_image_list:
        for id, in product_image_list:
            image = Image(store=store)
            query = """UPDATE image
                        SET image = p.full_image,
                            thumbnail =  p.image
                        FROM product p
                        WHERE p.id = %d AND image.id =  %d"""
            store.execute(query % (id, image.id))
            product = Product.get(id, store=store)
            product.sellable.image = image

    # Migrate all Service images to Image
    service_image_list = store.execute("""
                               SELECT id, image
                                   FROM service
                                   WHERE image != ''
                               ;""").get_all()
    if service_image_list:
        for id, image in service_image_list:
            image = Image(store=store,
                          image=image)
            service = Service.get(id, store=store)
            service.sellable.image = image

    # Remove 'image' colum from Product and Service
    # Also, remove 'full_image' from product
    store.execute("""
          ALTER TABLE product
              DROP COLUMN image;
          ALTER TABLE product
              DROP COLUMN full_image;
          ALTER TABLE service
              DROP COLUMN image;
          """)

    # Try to migrate CUSTOM_LOGO_FOR_REPORTS, if the filepath is valid on the
    # computer that's updating the schema
    image_path = store.execute("""
                       SELECT field_value
                           FROM parameter_data
                           WHERE field_name = 'CUSTOM_LOGO_FOR_REPORTS'
                       ;""").get_one()
    if image_path:
        image_path = image_path and image_path[0]
        try:
            image = PIL_Image.open(image_path)
        except Exception:
            # This probably means that the image wasn't on the computer
            # updating the schema or image is invalid.
            sysparam(store).update_parameter('CUSTOM_LOGO_FOR_REPORTS', '')
        else:
            f = StringIO.StringIO()
            image.save(f, 'png')
            image_domain = Image(store=store,
                                 image=f.getvalue())
            sysparam(store).update_parameter('CUSTOM_LOGO_FOR_REPORTS',
                                             image_domain.id)
            f.close()
