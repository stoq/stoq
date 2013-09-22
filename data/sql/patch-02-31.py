# -*- coding: utf-8 -*-

#
# Change the DELIVERY_SERVICE param from Sellable to Service.
# Changes for bug #4421
#

from stoqlib.domain.sellable import Sellable
from stoqlib.domain.service import Service
from stoqlib.domain.product import Product
from stoqlib.lib.parameters import sysparam

Product  # pylint: disable=W0104


def apply_patch(store):
    param_name = u'DELIVERY_SERVICE'

    # Get the param as a Sellable to get it's service
    sellable = sysparam().get_parameter_by_field(param_name, Sellable)

    if sellable and sellable.service:
        # Set the param to point to the Service.
        sysparam().update_parameter(
            param_name, unicode(sellable.service.id))
    elif sellable and sellable.product:
        # If the delivery service was a product, point it to the first
        # service available, if there's any service on the base. If not,
        # recreate the default delivery service.
        service = store.find(Service).order_by(Service.id)
        if service.count():
            sysparam().update_parameter(
                param_name, unicode(service[0].id))
        else:
            sysparam().create_delivery_service()

    store.commit(close=False)
