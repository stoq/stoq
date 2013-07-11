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
GnuCash importing
"""

import datetime
import decimal
import gzip
import logging
from xml.etree import ElementTree


from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.importers.importer import Importer

log = logging.getLogger(__name__)

GNC_NS = "http://www.gnucash.org/XML/gnc"
ACT_NS = "http://www.gnucash.org/XML/act"
TRN_NS = "http://www.gnucash.org/XML/trn"
TS_NS = "http://www.gnucash.org/XML/ts"
SPLIT_NS = "http://www.gnucash.org/XML/split"


def _gncns(tag):
    return '{%s}%s' % (GNC_NS, tag)


def _actns(tag):
    return '{%s}%s' % (ACT_NS, tag)


def _trnns(tag):
    return '{%s}%s' % (TRN_NS, tag)


def _tsns(tag):
    return '{%s}%s' % (TS_NS, tag)


def _splitns(tag):
    return '{%s}%s' % (SPLIT_NS, tag)


_account_types = {
    u'BANK': Account.TYPE_BANK,
    u'INCOME': Account.TYPE_INCOME,
    u'EXPENSE': Account.TYPE_EXPENSE,
    u'CASH': Account.TYPE_CASH,
    u'CREDIT': Account.TYPE_CREDIT,
    u'EQUITY': Account.TYPE_EQUITY,
    u'ASSET': Account.TYPE_ASSET,
}


class GnuCashXMLImporter(Importer):
    """Class to assist the process of importing gnucash files.

    """

    def __init__(self):
        Importer.__init__(self)
        self._accounts = {}
        self.items = []

    #
    # Public API
    #

    def feed_file(self, filename):
        if filename.endswith('.gz'):
            use_gzip = True
        elif filename.endswith('.xml'):
            use_gzip = False
        else:
            data = open(filename).read(4)
            if data == '<?xm':
                use_gzip = False
            elif data[:2] == '\x1f\x8b':
                use_gzip = True
            else:
                raise ValueError("Unknown content in filename: %s" % (
                    filename, ))

        fp = open(filename)
        if use_gzip:
            log.info("Looks like it's gzipped, unzipping")
            fp = gzip.GzipFile(mode='rb', fileobj=fp)
        return self.feed(fp)

    def feed(self, fp):
        doc = ElementTree.parse(fp)
        self.root = doc.getroot()
        items = []
        for node in self.root.findall(_gncns('book')):
            items.extend(node.findall(_gncns('account')))
            items.extend(node.findall(_gncns('transaction')))

        self._nodes = items

    def get_n_items(self):
        return len(self._nodes)

    def process_item(self, store, i):
        node = self._nodes[i]
        if node.tag == _gncns('account'):
            self._import_account(store, node)
        elif node.tag == _gncns('transaction'):
            self._import_transaction(store, node)

        return True
    # Private

    def _parse_date(self, data):
        data = data[:19]
        try:
            return datetime.datetime.strptime(data, '%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            pass

        log.info("Couldn't parse date: %r - %r" % (data, e))
        return None

    def _get_text(self, node, tag, default=None):
        child = node.find(tag)
        if child is not None:
            return child.text
        return default

    def _import_account(self, store, node):
        account_id = self._get_text(node, _actns('id'))
        account_name = self._get_text(node, _actns('name'))
        account_type = self._get_text(node, _actns('type'))
        parent = self._get_text(node, _actns('parent'))
        parent_account = self._accounts.get(parent)
        if account_type == 'ROOT':
            account = None
        else:
            account = store.find(Account, description=account_name).one()
            if account is None:
                account = Account(
                    account_type=_account_types.get(account_type, Account.TYPE_CASH),
                    description=account_name,
                    code=self._get_text(node, _actns('code')),
                    parent=parent_account,
                    store=store)
        self._accounts[account_id] = account

    def _import_transaction(self, store, node):
        date_text = self._get_text(node, '%s/%s' % (_trnns('date-posted'),
                                                    _tsns('date')))
        date = self._parse_date(date_text)

        splits = node.findall('%s/%s' % (_trnns('splits'),
                                         _trnns('split')))
        dest_node = splits[0]
        source_node = splits[1]

        source = self._get_text(source_node, _splitns('account'))
        source_account = self._accounts[source]
        assert source_account, ElementTree.tostring(source_node)

        dest = self._get_text(dest_node, _splitns('account'))
        dest_account = self._accounts[dest]
        assert dest_account, ElementTree.tostring(dest_node)

        text_value = self._get_text(dest_node, _splitns('value'))
        values = text_value.split('/', 2)
        value = decimal.Decimal(values[0]) / decimal.Decimal(values[1])

        if len(splits) != 2:
            # If we have a split to the same account, just merge them until
            # we support split transactions
            accounts = []
            diff = False
            for split_node in splits[2:]:
                split = self._get_text(split_node, _splitns('account'))
                if split != source:
                    diff = True
                accounts.append(self._accounts[split])

            if diff:
                log.info("Can't do splits to different accounts: %s->%s" % (
                    dest_account.description, ', '.join(repr(a.description)
                                                        for a in accounts)))
                return

        at = AccountTransaction(
            account=dest_account,
            source_account=source_account,
            description=self._get_text(node, _trnns('description')),
            code=self._get_text(node, _trnns('num')),
            date=date,
            value=value,
            store=store)
        at.sync()
