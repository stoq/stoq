# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s):  Evandro Vale Miquelito   <evandro@async.com.br>
##
""" Create gift certificates for an example database"""

from stoqlib.database.runtime import new_transaction
from stoqlib.domain.examples import log
from stoqlib.domain.giftcertificate import GiftCertificateType, GiftCertificate
from stoqlib.domain.interfaces import ISellable
from stoqlib.domain.sellable import BaseSellableInfo, ASellable

MAX_GIFTCERTIFICATE_NUMBER = 2

def create_giftcertificates():
    log.info('Creating gift certificates')
    trans = new_transaction()

    statuses = [ASellable.STATUS_SOLD,
                ASellable.STATUS_AVAILABLE]

    sellable_data = [dict(description='Christmas Gift Certificate',
                          price=430),
                     dict(description='Passover Gift Certificate',
                          price=650)]

    # Creating products and facets
    for index in range(MAX_GIFTCERTIFICATE_NUMBER):
        sellable_args = sellable_data[index]
        sellable_info = BaseSellableInfo(connection=trans, **sellable_args)

        GiftCertificateType(connection=trans,
                            base_sellable_info=sellable_info)
        certificate = GiftCertificate(connection=trans)

        status = statuses[index]
        certificate.addFacet(ISellable, connection=trans,
                             tax_constant=None,
                             base_sellable_info=sellable_info,
                             status=status)
    trans.commit()

if __name__ == "__main__":
    create_giftcertificates()
