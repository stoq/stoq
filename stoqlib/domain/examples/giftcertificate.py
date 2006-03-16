#!/usr/bin/env python
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

from stoqlib.domain.giftcertificate import GiftCertificateType, GiftCertificate
from stoqlib.domain.interfaces import ISellable
from stoqlib.domain.sellable import BaseSellableInfo, AbstractSellable
from stoqlib.lib.runtime import new_transaction, print_msg

MAX_GIFTCERTIFICATE_NUMBER = 2

def create_giftcertificates():
    print_msg('Creating gift certificates...', break_line=False)
    conn = new_transaction()

    general_data = [dict(code='GC23', 
                         status=AbstractSellable.STATUS_SOLD),
                    dict(code='GC34',
                         status=AbstractSellable.STATUS_AVAILABLE)]

    sellable_data = [dict(description='Christmas Gift Certificate',
                          price=430),
                     dict(description='Passover Gift Certificate',
                          price=650)]

    # Creating products and facets
    for index in range(MAX_GIFTCERTIFICATE_NUMBER):
        sellable_args = sellable_data[index]
        sellable_info = BaseSellableInfo(connection=conn, **sellable_args)

        cert_type = GiftCertificateType(connection=conn,
                                        base_sellable_info=sellable_info)
        certificate = GiftCertificate(connection=conn)

        cert_data = general_data[index]
        certificate.addFacet(ISellable, connection=conn,
                             base_sellable_info=sellable_info,
                             **cert_data)
    conn.commit()
    print_msg('done.')

if __name__ == "__main__":
    create_giftcertificates()
