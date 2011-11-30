# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source
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
OFX importing
"""

import datetime
import decimal
import sgmllib

from kiwi.log import Logger

from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.importers.importer import Importer
from stoqlib.lib.parameters import sysparam


log = Logger('ofximporter')


class OFXTagParser(sgmllib.SGMLParser):
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)

        self.transactions = []
        self.fi = None
        self.account_id = None
        self.account_type = None

        self._is_statement = False
        self._is_fi = False
        self._is_account_id = False
        self._is_account_type = False
        self._tag = None
        self._tags = {}

    def unknown_starttag(self, tag, attrs):
        self._tag = tag

        if tag == 'stmttrn':
            self._is_statement = True
        elif tag == 'fi':
            self._is_fi = True
        elif tag == 'acctid':
            self._is_account_id = True
        elif tag == 'accttype':
            self._is_account_type = True

    def unknown_endtag(self, tag):
        if tag == 'stmttrn':
            self._is_statement = False
            self.transactions.append(self._tags)
            self._tags = {}
        if tag == 'fi':
            self._is_fi = False
            self.fi = {'org': self._tags['org'],
                       'fid': self._tags['fid']}
            self._tags = {}

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        if self._tag == 'acctid':
            self.account_id = data
        elif self._tag == 'accttype':
            self.account_type = data
        else:
            self._tags[self._tag] = data


class OFXImporter(Importer):
    """Class to assist the process of importing ofx files.

    """

    def __init__(self):
        Importer.__init__(self)
        self._headers = {}

    #
    # Public API
    #

    def feed(self, fp, filename='<stdin>'):
        data = fp.read()
        if '\r' in data:
            data = data.replace('\r\n', '\n')
            data = data.replace('\r', '\n')
        lines = data.split('\n')
        for i, line in enumerate(lines):
            if not line:
                continue
            if line.startswith('<OFX>'):
                self._parse_tags(lines[i:])
                break
            else:
                header, value = line.split(':', 1)
                self._headers[header] = value

    def _parse_tags(self, data):
        self.tp = OFXTagParser()
        self.tp.feed('\n'.join(data))

    def _parse_number(self, data):
        data = data.strip()
        data = data.replace(',', '.')

        try:
            number = decimal.Decimal(data)
        except decimal.InvalidOperation:
            log.info("Couldn't parse number: %r" % (data, ))
            number = 0
        return number

    def _parse_string(self, data):
        return unicode(data, self._headers['CHARSET']).encode('utf-8')

    def _parse_date(self, data):
        # BB Juridica: 20110207
        # BB Fisica:   20110401120000[-3:BRT]
        data = data.strip()
        for length, format in [(14, '%Y%m%d%H%M%S'),
                               (8, "%Y%m%d")]:
            short = data[:length]
            try:
                return datetime.datetime.strptime(
                    short, format)
            except ValueError:
                continue

        log.info("Couldn't parse date: %r" % (data, ))
        return None

    def before_start(self, trans):
        account = Account.selectOneBy(
            connection=trans,
            code=self.tp.account_id)
        if account is None:
            account = Account(description=self.get_account_id(),
                              code=self.tp.account_id,
                              account_type=Account.TYPE_BANK,
                              parent=sysparam(trans).BANKS_ACCOUNT,
                              connection=trans)
        self.account_id = account.id
        self.source_account_id = sysparam(trans).IMBALANCE_ACCOUNT.id
        self.skipped = 0

    def get_n_items(self):
        return len(self.tp.transactions)

    def process_item(self, trans, i):
        t = self.tp.transactions[i]
        date = self._parse_date(t['dtposted'])
        # Do not import transactions with broken dates
        if date is None:
            self.skipped += 1
            return False

        value = self._parse_number(t['trnamt'])
        if value == 0:
            self.skipped += 1
            # We can't import transactions with a value = 0, skip it.
            return False
        source_account = Account.get(self.source_account_id, trans)
        account = Account.get(self.account_id, trans)

        code = self._parse_string(t['checknum'])
        if AccountTransaction.selectBy(date=date, code=code, value=value,
                                       connection=trans):
            # Skip already present transactions
            self.skipped += 1
            return False
        t = AccountTransaction(source_account=source_account,
                               account=account,
                               description=self._parse_string(t['memo']),
                               code=code,
                               value=value,
                               date=date,
                               connection=trans)
        t.sync()
        return True

    def when_done(self, trans):
        log.info("Imported %d transactions" % (len(self.tp.transactions), ))
        if self.skipped:
            log.info("Couldn't parse %d transactions" % (self.skipped, ))

    def get_account_id(self):
        if self.tp.fi:
            return '%s - %s' % (self.tp.fi['org'],
                                self.tp.account_type)
        return self.tp.account_type

if __name__ == '__main__':
    import sys
    ofx = OFXImporter()
    ofx.feed(sys.argv[1])
    ofx.process()
