# -*- coding: utf-8 -*-

#
# Change the DELIVERY_SERVICE param from Sellable to Service.
# Changes for bug #4421
#

from stoqlib.domain.parameter import ParameterData
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.service import Service
from stoqlib.domain.product import Product
from stoqlib.lib.parameters import sysparam

Product # pyflakes

def apply_patch(trans):

    param_name = 'DELIVERY_SERVICE'

    # Get the param as a Sellable to get it's service
    sellable = sysparam(trans).get_parameter_by_field(param_name, Sellable)

    if sellable and sellable.service:
        # Set the param to point to the Service.
        sysparam(trans).update_parameter(param_name, sellable.service.id)
    elif sellable and sellable.product:
        # If the delivery service was a product, point it to the first
        # service available, if there's any service on the base. If not,
        # recreate the default delivery service.
        service = Service.select(connection=trans).orderBy(Service.q.id)
        if service.count():
            sysparam(trans).update_parameter(param_name, service[0].id)
        else:
            sysparam(trans).create_delivery_service()

    trans.commit(close=False)
