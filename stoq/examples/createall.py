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
"""
stoq/examples/createall.py:

    Create all objects for an example database used by Stoq applications.
"""

import sys

from stoq.lib.runtime import print_msg, set_verbose
from stoq.examples.person import create_persons
from stoq.examples.product import create_products
from stoq.examples.service import create_services
from stoq.examples.sale import create_sales
from stoq.examples.payment import create_payments
from stoq.examples.purchase import create_purchases
from stoq.examples.giftcertificate import create_giftcertificates
from stoq.examples.devices import create_device_settings

VERBOSE = '-v' in sys.argv


def create():
    print_msg('Creating example database...')
    create_persons()
    create_products()
    create_services()
    create_payments()
    create_sales()
    create_purchases()
    create_giftcertificates()
    create_device_settings()
    print_msg('done.')

if __name__ == "__main__":
    set_verbose(VERBOSE)
    create()

