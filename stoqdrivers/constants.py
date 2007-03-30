# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
"""
StoqDrivers constants
"""

from stoqdrivers.enum import PaymentMethodType, TaxType, UnitType
from stoqdrivers.translation import stoqdrivers_gettext

_ = lambda msg: stoqdrivers_gettext(msg)

# TODO: Improve these descriptions
_constant_descriptions = {
    UnitType.WEIGHT: _(u"Weight unit"),
    UnitType.METERS: _(u"Meters unit"),
    UnitType.LITERS: _(u"Liters unit"),
    UnitType.EMPTY: _(u"Empty unit"),
    TaxType.ICMS: _(u"ICMS"),
    TaxType.SUBSTITUTION: _(u"Substitution"),
    TaxType.EXEMPTION: _(u"Exemption"),
    TaxType.NONE: _(u"No tax"),
    TaxType.SERVICE: _(u"Service tax"),
    PaymentMethodType.MONEY: _(u"Money Payment Method"),
    PaymentMethodType.CHECK: _(u"Check Payment Method"),
    PaymentMethodType.DEBIT_CARD: _(u"Debit card Payment Method"),
    PaymentMethodType.CREDIT_CARD: _(u"Credit card Payment Method"),
    PaymentMethodType.BILL: _(u"Bill Payment Method"),
    PaymentMethodType.FINANCIAL: _(u"Financial Payment Method"),
    PaymentMethodType.GIFT_CERTIFICATE: _(u"Gift certificate Payment Method"),
    }

def describe_constant(constant_id):
    """ Given the constant identifier, return a short string describing it """
    global _constant_descriptions
    if not constant_id in _constant_descriptions:
        raise ValueError("The constant by id %r doesn't exists or there "
                         "is no description for it." % constant_id)
    return _constant_descriptions[constant_id]
