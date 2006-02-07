#!/usr/bin/env python
# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
##  Author(s):  Evandro Vale Miquelito   <evandro@async.com.br>
##
"""
stoq/examples/giftcertificate.py:

    Create gift certificates for an example database.
"""

from stoq.domain.giftcertificate import GiftCertificateType, GiftCertificate
from stoq.domain.interfaces import ISellable
from stoq.domain.sellable import BaseSellableInfo, AbstractSellable
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
                          price=430.00),
                     dict(description='Passover Gift Certificate',
                          price=650.00)]

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
