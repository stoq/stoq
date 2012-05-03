from stoqlib.domain.sale import SaleItem, Delivery
from stoqlib.domain.address import Address
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


def apply_patch(trans):
    # Create Delivery table and add a reference on SaleItem
    trans.query("""
          CREATE TABLE delivery (
              id serial NOT NULL PRIMARY KEY,
              te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
              te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),

              status integer CONSTRAINT valid_status
                  CHECK (status >= 0 AND status < 3),
              open_date timestamp,
              deliver_date timestamp,
              receive_date timestamp,
              tracking_code text,
              address_id bigint REFERENCES address(id),
              transporter_id bigint REFERENCES transporter(id),
              service_item_id bigint REFERENCES sale_item(id)
          );

          ALTER TABLE sale_item
              ADD COLUMN delivery_id bigint REFERENCES delivery(id);
          """)

    # Migrate all deliveries
    deliveries = trans.queryAll('SELECT original_id, address '
                                'FROM sale_item_adapt_to_delivery;')
    address_dict = {}
    for id, address in deliveries:
        sale_item = SaleItem.get(id, trans)

        delivery = address_dict.get(address, None)
        if not delivery:
            sale = sale_item.sale

            # Use close_date to mimic Delivery status behavior as we didn't
            # store that information before. If the sale status is closed,
            # we mark the delivery as delivered, but if it's just
            # confirmed, we just mark it delivering.
            status = (Delivery.STATUS_RECEIVED if sale.close_date else
                      Delivery.STATUS_SENT)

            service_item = _get_service_item(sale, trans)

            try:
                address = _get_or_create_address_by_str(address, sale.client,
                                                        trans)
            except Exception:
                # Don't know if this is necessary. Since we are doing an ugly
                # workaround to get or generate the address_string, it's better
                # to prevent any kind of errors and just set address to None.
                address = None

            delivery = Delivery(
                connection=trans,
                status=status,
                transporter=sale.transporter,
                deliver_date=sale.confirm_date,
                receive_date=sale.close_date,
                service_item=service_item,
                address=address,
                )
            address_dict[address] = delivery

        delivery.add_item(sale_item)

    # Drop DeliveryItem and SaleItemAdaptToDelivery
    trans.query('DROP TABLE delivery_item; '
                'DROP TABLE sale_item_adapt_to_delivery;')


def _get_address_string(address):
    # Just copying this function from domain/address.py to avoid problems if
    # this changes in the future.
    if address.street and address.streetnumber and address.district:
        return u'%s %s, %s' % (address.street, address.streetnumber,
                               address.district)
    elif address.street and address.district:
        return u'%s %s, %s' % (address.street, _(u'N/A'), address.district)
    elif address.street and address.streetnumber:
        return u'%s %s' % (address.street, address.streetnumber)
    elif address.street:
        return address.street

    return u''


def _get_or_create_address_by_str(address, client, trans):
    for c_address in client.person.addresses:
        # Most of cases the client address didn't change, therefore they have
        # the same get_address_string form
        if address == _get_address_string(c_address):
            return c_address

    if ',' in address:
        street, district = address.split(',')
        district = district.strip()
    else:
        street = address
        district = None

    if street.endswith('N/A'):
        streetnumber = None
        street = street[:-3].strip()
    else:
        streetnumber = None
        for i in range(len(address)):
            try:
                # Try to get streetnumber from the end of address
                streetnumber = int(street[-i:])
            except ValueError:
                if i:
                    # If any number retrieved, remove it from street
                    street = street[:-i].strip()
                break

    # This wasn't stored on delivery before
    city_location = client.get_main_address.city_location

    return Address(
        connection=trans,
        city_location=city_location,
        street=street,
        streetnumber=streetnumber,
        district=district,
        )


def _get_service_item(sale, trans):
    delivery_service = sysparam(trans).DELIVERY_SERVICE
    for item in sale.get_items():
        if item.sellable == delivery_service.sellable:
            # For most of cases, if the user didn't change the delivery
            # service, this should be all we need
            return item

    services = [item for item in sale.get_items() if item.sellable.service]
    if len(services) == 1:
        # If only one, that's for sure the delivery service
        return services[0]

    for service in services:
        # try to find the delivery service by it's price
        if service.base_price == delivery_service.sellable.price:
            return service

    # Try to figure out what's the service_item by diffing their prices
    diff_dict = dict(
        [(abs(delivery_service.sellable.price - service.base_price), service)
         for service in services]
        )
    min_ = min(diff_dict.keys())
    return diff_dict[min_]
