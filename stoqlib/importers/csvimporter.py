# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source
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
## Author(s):       Johan Dahlin                <jdahlin@async.com.br>
##
##

"""
CSV import classes
"""

import csv
import datetime
import time

from kiwi.python import namedAny

from stoqlib.database.runtime import new_transaction

class CSVRow(object):
    """A row in a CSV file
    """
    def __init__(self, item, field_names):
        self.fields = []
        for i, field in enumerate(item):
            #XXX: we expect to receive unicode data
            setattr(self, field_names[i], unicode(field))
            self.fields.append(field_names[i])

    def __repr__(self):
        return '<CSV line %s>' % ', '.join(
            ['%s=%r' % (f, getattr(self, f)) for f in self.fields])

class CSVImporter(object):
    """Class to assist the process of importing csv files.

    @cvar fields: field names, a list of strings
    @cvar optional_fields: optional field names, a list of strings
    @cvar dialect: optional, csv dialect, defaults to excel
    """
    fields = []
    optional_fields = []
    dialect = 'excel'

    # Available importers, the value is relative to stoqlib.importers
    _available_importers = {
        'client': 'clientimporter.ClientImporter',
        'employee': 'employeeimporter.EmployeeImporter',
        'product': 'productimporter.ProductImporter',
        'service': 'serviceimporter.ServiceImporter',
        'supplier': 'supplierimporter.SupplierImporter',
        'transporter': 'transporterimporter.TransporterImporter',
        'branch': 'branchimporter.BranchImporter',
        'creditprodvider': 'creditprodviderimporter.CreditProdviderImporter',
        'purchase': 'purchaseimporter.PurchaseImporter',
        'sale': 'saleimporter.SaleImporter',
        'transfer': 'transferimporter.TransferImporter',
        }

    def __init__(self, lines=500, dry=False):
        """
        Create a new CSVImporter object.
        @param lines: see L{set_lines_per_commit}
        @param dry: see L{set_dry}
        """
        self.lines = lines
        self.dry = dry

    #
    # Public API
    #

    def feed_file(self, filename, skip=0):
        """Feeds csv data from filename to the importer
        @param filename: filename
        @param skip: optional, number of rows to initially skip
        """
        self.feed(open(filename), filename, skip=skip)

    def feed(self, iterable, filename='<stdin>', skip=0):
        """Feeds csv data from an iterable
        @param iterable: an iterable
        @param filename: optinal, name of input file
        @param skip: optional, number of rows to initially skip
        """
        field_names = self.fields + self.optional_fields

        t = time.time()
        trans = new_transaction()
        self.before_start(trans)
        lineno = 1
        for item in self.read(iterable):
            if skip > lineno:
                lineno += 1
                continue

            if not item or item[0].startswith('%'):
                lineno += 1
                continue
            if len(item) < len(self.fields):
                raise ValueError(
                    "line %d in file %s has %d fields, but we need at "
                    "least %d fields to be able to process it" % (
                    lineno, filename, len(item), len(self.fields)))
            if len(item) > len(field_names):
                raise ValueError(
                    "line %d in file %s has %d fields, but we can at most "
                    "handle %d fields, fields=%r" % (
                    lineno, filename, len(item), len(field_names), item))

            row = CSVRow(item, field_names)
            try:
                self.process_one(row, row.fields, trans)
            except Exception, e:
                print
                print 'Error while processing row %d %r' % (lineno, row,)
                print
                raise

            if self.lines != -1:
                if lineno % self.lines == 0:
                    if not self.dry:
                        trans.commit()
                    t2 = time.time()
                    print '%s Imported %d entries in %2.2f sec total=%d' % (
                        datetime.datetime.now().strftime('%T'), self.lines,
                        t2-t, lineno)
                    t = t2
                    trans = new_transaction()

            lineno += 1

        self.when_done(trans)

        if not self.dry:
            trans.commit(close=True)

    def parse_date(self, data):
        return datetime.datetime(*map(int, data.split('-')))

    def parse_multi(self, domain_class, field, trans):
        if field == '*':
            field_values = domain_class.select(connection=trans)
        else:
            field_values = [domain_class.get(int(field_id), connection=trans)
                            for field_id in field.split('|')]
        return field_values

    def set_lines_per_commit(self, lines):
        """Sets the number of lines which should be parsed between commits.
        Defaults to 500. -1 means that the whole file should be parsed
        before committing
        @param lines: number of lines or
        """
        self.lines = lines

    def set_dry(self, dry):
        """Tells the CSVImporter to run in dry mode, eg without committing
        anything.
        @param dry: dry mode
        """
        self.dry = dry

    #
    # Classmethods
    #

    @classmethod
    def get_by_type(cls, importer_type):
        """Gets an importers class, instantiates it returns it
        @param importer_type: an importer
        @type importer_type: string
        @returns: an importer instance
        @type: L{CSVImporter} subclass
        """
        if not importer_type in cls._available_importers:
            raise ValueError("Invalid importer %s, must be one of %s" % (
                importer_type, ', '.join(sorted(cls._available_importers))))
        name = cls._available_importers[importer_type]
        importer_cls = namedAny('stoqlib.importers.%s' % (name,))
        return importer_cls()

    #
    # Override this in a subclass
    #

    def process_one(self, row, fields, trans):
        """Processes one line in a csv file, you can access the columns
        using attributes on the data object.
        @param row: object representing a row in the input
        @param fields: a list of fields set in data
        @param trans: a database transaction
        """
        raise NotImplementedError

    def read(self, iterable):
        """This can be overridden by as subclass which wishes to specialize
        the CSV reader.
        @param iterable: a sequence of lines which are going to be read
        @returns: a sequence of parsed items
        """
        return csv.reader(iterable, dialect=self.dialect)

    def before_start(self, trans):
        """This is called before all the lines are parsed but
        after creating a transaction.
        """

    def when_done(self, trans):
        """This is called after all the lines are parsed but
        before committing.
        """
