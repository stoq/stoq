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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

"""
CSV import classes
"""

import csv
import datetime
import time

from stoqlib.database.runtime import new_store
from stoqlib.importers.importer import Importer
from stoqlib.lib.dateutils import localdate


class CSVRow(object):
    """A row in a CSV file
    """
    def __init__(self, item, field_names):
        self.fields = []
        for i, field in enumerate(item):
            # XXX: we expect to receive unicode data
            setattr(self, field_names[i], unicode(field, 'utf-8'))
            self.fields.append(field_names[i])

    def __repr__(self):
        return '<CSV line %s>' % ', '.join(
            ['%s=%r' % (f, getattr(self, f)) for f in self.fields])


class CSVImporter(Importer):
    """Class to assist the process of importing csv files.

    :cvar fields: field names, a list of strings
    :cvar optional_fields: optional field names, a list of strings
    :cvar dialect: optional, csv dialect, defaults to excel
    """
    fields = []
    optional_fields = []
    dialect = 'excel'

    def __init__(self, lines=500, dry=False):
        """
        Create a new CSVImporter object.
        :param lines: see :class:`set_lines_per_commit`
        :param dry: see :class:`set_dry`
        """
        Importer.__init__(self, items=lines, dry=dry)
        self.lines = lines

    #
    # Public API
    #

    def feed(self, fp, filename='<stdin>'):
        store = new_store()
        self.before_start(store)
        store.commit(close=True)
        self.lineno = 1
        self.rows = list(csv.reader(fp, dialect=self.dialect))

    def get_n_items(self):
        return len(self.rows)

    def process_item(self, store, item_no):
        t = time.time()
        item = self.rows[item_no]
        if not item or item[0].startswith('%'):
            self.lineno += 1
            return False
        if len(item) < len(self.fields):
            raise ValueError(
                "line %d in file %s has %d fields, but we need at "
                "least %d fields to be able to process it" % (self.lineno,
                                                              self.filename,
                                                              len(item),
                                                              len(self.fields)))

        field_names = self.fields + self.optional_fields
        if len(item) > len(field_names):
            raise ValueError(
                "line %d in file %s has %d fields, but we can at most "
                "handle %d fields, fields=%r" % (self.lineno,
                                                 self.filename,
                                                 len(item),
                                                 len(field_names),
                                                 item))

        row = CSVRow(item, field_names)
        try:
            self.process_one(row, row.fields, store)
        except Exception:
            print()
            print('Error while processing row %d %r' % (self.lineno, row, ))
            print()
            raise

        if self.items != -1:
            if self.lineno % self.items == 0:
                t2 = time.time()
                print('%s Imported %d entries in %2.2f sec total=%d' % (
                    datetime.datetime.now().strftime('%T'), self.items,
                    t2 - t, self.lineno))
                t = t2

        self.lineno += 1
        return True

    def parse_date(self, data):
        return localdate(*map(int, data.split('-')))

    def parse_multi(self, domain_class, field, store):
        if field == '*':
            field_values = store.find(domain_class)
        else:
            items = store.find(domain_class).order_by(domain_class.te_id)
            field_values = [items[int(field_id) - 1]
                            for field_id in field.split('|')]
        return field_values

    #
    # Override this in a subclass
    #

    def process_one(self, row, fields, store):
        """Processes one line in a csv file, you can access the columns
        using attributes on the data object.
        :param row: object representing a row in the input
        :param fields: a list of fields set in data
        :param store: a store
        """
        raise NotImplementedError

    def read(self, iterable):
        """This can be overridden by as subclass which wishes to specialize
        the CSV reader.
        :param iterable: a sequence of lines which are going to be read
        :returns: a sequence of parsed items
        """
