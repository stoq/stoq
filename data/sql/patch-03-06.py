import StringIO

from PIL import Image as PIL_Image
from storm.references import Reference

from stoqlib.database.properties import BLOBCol, UnicodeCol, IntCol
from stoqlib.migration.parameter import update_parameter
from stoqlib.migration.domainv1 import Domain


class Image(Domain):
    __storm_table__ = 'image'

    image = BLOBCol(default=None)
    thumbnail = BLOBCol(default=None)
    description = UnicodeCol(default=u'')


class Sellable(Domain):
    __storm_table__ = 'sellable'
    image_id = IntCol()


class Product(Domain):
    __storm_table__ = 'product'
    sellable_id = IntCol()
    sellable = Reference(sellable_id, Sellable.id)


class Service(Domain):
    __storm_table__ = 'service'
    sellable_id = IntCol()
    sellable = Reference(sellable_id, Sellable.id)


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
            product.sellable.image_id = image.id

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
            service.sellable.image_id = image.id

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
            update_parameter(store, u'CUSTOM_LOGO_FOR_REPORTS', u'')
        else:
            f = StringIO.StringIO()
            image.save(f, 'png')
            image_domain = Image(store=store,
                                 image=f.getvalue())
            update_parameter(store,
                             u'CUSTOM_LOGO_FOR_REPORTS',
                             unicode(image_domain.id))
            f.close()
