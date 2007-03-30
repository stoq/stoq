# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
""" Create all objects for an example database used by Stoq applications"""

from kiwi.environ import environ
from stoqlib.domain.examples import log
from stoqlib.domain.examples.person import create_people, set_person_utilities
from stoqlib.importers.clientimporter import ClientImporter
from stoqlib.importers.employeeimporter import EmployeeImporter
from stoqlib.importers.productimporter import ProductImporter
from stoqlib.importers.serviceimporter import ServiceImporter
from stoqlib.importers.supplierimporter import SupplierImporter
from stoqlib.importers.transporterimporter import TransporterImporter
from stoqlib.domain.examples.sale import create_sales
from stoqlib.domain.examples.purchase import create_purchases
from stoqlib.domain.examples.giftcertificate import create_giftcertificates
from stoqlib.domain.examples.devices import create_device_settings

def _import_one(klass, filename):
    imp = klass()
    imp.feed_file(environ.find_resource('csv', filename))

def create(utilities=False):
    log.info('Creating example database')
    create_people()
    _import_one(SupplierImporter, 'suppliers.csv')
    _import_one(TransporterImporter, 'transporters.csv')
    _import_one(EmployeeImporter, 'employees.csv')
    _import_one(ClientImporter, 'clients.csv')
    if utilities:
        set_person_utilities()
    create_device_settings()
    _import_one(ProductImporter, 'products.csv')
    _import_one(ServiceImporter, 'services.csv')
    create_sales()
    create_purchases()
    create_giftcertificates()
