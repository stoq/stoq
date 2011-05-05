# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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

from cStringIO import StringIO
import datetime
from decimal import Decimal
import os

from stoqlib.database.runtime import new_transaction
from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.importers.ofximporter import OFXImporter
from stoqlib.lib.parameters import sysparam


OFX_DATA = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE
<OFX>
<SIGNONMSGSRSV1>
        <SONRS>
                <STATUS>
                        <CODE>0</CODE>
                        <SEVERITY>INFO</SEVERITY>
                </STATUS>
                <DTSERVER>19990201
                <LANGUAGE>POR
                <DTACCTUP>19990201
                <FI>
                        <ORG>Bank
                        <FID>001
                </FI>
        </SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
        <STMTTRNRS>
                <TRNUID>0
                <STATUS>
                        <CODE>0
                        <SEVERITY>INFO
                </STATUS>
                <STMTRS>
                        <CURDEF>BRL
                        <BANKACCTFROM>
                                <BANKID>001
                                <ACCTID>1234
                                <ACCTTYPE>CHECKING
                        </BANKACCTFROM>
                        <BANKTRANLIST>

                                <STMTTRN>
                                        <TRNTYPE>CREDIT
                                        <DTPOSTED>19991001
                                        <TRNAMT>50.0000
                                        <FITID>90068259
                                        <CHECKNUM>90068259
                                        <MEMO>A Transaction
                                </STMTTRN>

                                <STMTTRN>
                                        <TRNTYPE>CREDIT
                                        <DTPOSTED>19991001
                                        <TRNAMT>-5.00
                                        <FITID>90068259
                                        <CHECKNUM>90068259
                                        <MEMO>Banco taxa 10%
                                </STMTTRN>

                        </BANKTRANLIST>
                        <LEDGERBAL>
                                <BALAMT>0
                                <DTASOF>19990228
                        </LEDGERBAL>
                </STMTRS>
        </STMTTRNRS>
</BANKMSGSRSV1>
</OFX>"""

class OFXImporterTest(DomainTest):
    def testOFXImport(self):
        ofx = OFXImporter()
        ofx.parse(StringIO(OFX_DATA))
        imbalance_account = sysparam(self.trans).IMBALANCE_ACCOUNT
        trans = new_transaction()
        account = ofx.import_transactions(trans, imbalance_account)
        self.failUnless(account)
        self.assertEquals(account.description, "Bank - CHECKING")
        self.assertEquals(account.code, "1234")
        self.assertEquals(account.transactions.count(), 2)
        t1, t2 = sorted(account.transactions)
        self.assertEquals(t1.value, -5)
        self.assertEquals(t1.code, '90068259')
        self.assertEquals(t2.value, 50)
        self.assertEquals(t2.code, '90068259')
