# -*- coding: utf-8 -*-

#
# Change the DELIVERY_SERVICE param from Sellable to Service.
# Changes for bug #4421
#

from stoqlib.domain.parameter import ParameterData
from stoqlib.domain.sellable import Sellable
from stoqlib.lib.parameters import sysparam

def apply_patch(trans):

    param_name = 'DELIVERY_SERVICE'

    # Get the param as a Sellable to get it's service
    sellable = sysparam(trans).get_parameter_by_field(param_name, Sellable)

    if sellable and sellable.service:
        # Set the param to point to the Service.
        sysparam(trans).update_parameter(param_name, service.id)
    elif sellable and sellable.product:
        # If it was a product, remove it and let the parameters create
        # another one. That new one will be a service for sure.
        param = ParameterData.selectOneBy(connection=trans,
                                          field_name=param_name)
        if param:
            ParameterData.delete(param.id, connection=trans)
            trans.commit(close=False)

        sysparam(trans).ensure_delivery_service()

