# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2011 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import datetime
import time

from kiwi.log import Logger
from kiwi.python import namedAny
import pango

from stoqlib.database.runtime import new_transaction

log = Logger('stoqlib.importer')
create_log = Logger('stoqlib.importer.create')

# pango is not used, but we're importing it so that
# python changes it's default encoding to utf-8,
# we could also call sys.setdefaultencoding, but then
# we're have to reload(sys) since it's deleted by site
pango  # pyflakes

_available_importers = {
    'account.ofx': 'ofximporter.OFXImporter',
    'branch.csv': 'branchimporter.BranchImporter',
    'client.csv': 'clientimporter.ClientImporter',
    'creditprodvider.csv': 'creditprodviderimporter.CreditProdviderImporter',
    'employee.csv': 'employeeimporter.EmployeeImporter',
    'gnucash.xml': 'gnucashimporter.GnuCashXMLImporter',
    'product.csv': 'productimporter.ProductImporter',
    'purchase.csv': 'purchaseimporter.PurchaseImporter',
    'sale.csv': 'saleimporter.SaleImporter',
    'service.csv': 'serviceimporter.ServiceImporter',
    'supplier.csv': 'supplierimporter.SupplierImporter',
    'supplier': 'supplierimporter.SupplierImporter',
    'transfer.csv': 'transferimporter.TransferImporter',
    'transporter.csv': 'transporterimporter.TransporterImporter',
}


class Importer(object):
    """Class to assist the process of importing csv files.

    """

    def __init__(self, items=500, dry=False):
        """
        Create a new Importer object.
        @param items: see L{set_items_per_commit}
        @param dry: see L{set_dry}
        """
        self.items = items
        self.dry = dry

    def feed_file(self, filename):
        """Feeds csv data from filename to the importer
        @param filename: filename
        """
        self.filename = filename
        self.feed(open(filename), filename)

    def set_items_per_commit(self, items):
        """Sets the number of items which should be parsed between commits.
        Defaults to 500. -1 means that the whole file should be parsed
        before committing
        @param items: number of items or
        """
        self.n_items = items

    def set_dry(self, dry):
        """Tells the CSVImporter to run in dry mode, eg without committing
        anything.
        @param dry: dry mode
        """
        self.dry = dry

    def process(self, trans=None):
        """Do the main logic, create transactions, import items etc"""
        n_items = self.get_n_items()
        log.info('Importing %d items' % (n_items, ))
        create_log.info('ITEMS:%d' % (n_items, ))
        t1 = time.time()

        imported_items = 0
        if not trans:
            trans = new_transaction()
        self.before_start(trans)
        for i in range(n_items):
            if self.process_item(trans, i):
                create_log.info('ITEM:%d' % (i + 1, ))
                imported_items += 1
            if not self.dry and i + 1 % 100 == 0:
                trans.commit(close=True)
                trans = new_transaction()

        if not self.dry:
            trans.commit(close=True)
            trans = new_transaction()

        self.when_done(trans)

        if not self.dry:
            trans.commit(close=True)

        t2 = time.time()
        log.info('%s Imported %d entries in %2.2f sec' % (
            datetime.datetime.now().strftime('%T'), n_items,
            t2 - t1))
        create_log.info('IMPORTED-ITEMS:%d' % (imported_items, ))

    def feed(self, fp, filename='<stdin>'):
        """Feeds csv data from an iterable
        @param fp: a file descriptor
        @param filename: optinal, name of input file
        """
        raise NotImplementedError

    def get_n_items(self):
        raise NotImplementedError

    def process_item(self, transaction, item_no):
        """
        @returns True if the item was imported, False if not
        """
        raise NotImplementedError

    #
    # Optional to implement
    #

    def before_start(self, trans):
        """This is called before all the lines are parsed but
        after creating a transaction.
        """

    def when_done(self, trans):
        """This is called after all the lines are parsed but
        before committing.
        """


def get_by_type(importer_type):
    """Gets an importers class, instantiates it returns it
    @param importer_type: an importer
    @type importer_type: string
    @returns: an importer instance
    @type: L{Importer} subclass
    """

    if not importer_type in _available_importers:
        raise ValueError("Invalid importer %s, must be one of %s" % (
            importer_type, ', '.join(sorted(_available_importers))))
    name = _available_importers[importer_type]
    cls = namedAny('stoqlib.importers.%s' % (name, ))
    return cls()
