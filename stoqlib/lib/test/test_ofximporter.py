# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2011 Async Open Source <http://www.async.com.br>
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
from decimal import Decimal
import operator

from stoqlib.domain.account import Account
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.importers.ofximporter import OFXImporter


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
                                        <FITID>90068258
                                        <CHECKNUM>90068258
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

OFX_DATA2 = """OFXHEADER:100DATA:OFXSGMLVERSION:102SECURITY:NONEENCODING:USASCIICHARSET:1252COMPRESSION:NONEOLDFILEUID:NONENEWFILEUID:NONE<OFX>
   <SIGNONMSGSRSV1>
      <SONRS>
         <STATUS>
            <CODE>0</CODE>
            <SEVERITY>INFO</SEVERITY>
         </STATUS>
         <DTSERVER>20110505120000[-3:BRT]</DTSERVER>
         <LANGUAGE>POR</LANGUAGE>
         <FI>
            <ORG>Banco do Brasil</ORG>
            <FID>1</FID>
         </FI>
      </SONRS>
   </SIGNONMSGSRSV1>
   <BANKMSGSRSV1>
      <STMTTRNRS>
         <TRNUID>1</TRNUID>
         <STATUS>
            <CODE>0</CODE>
            <SEVERITY>INFO</SEVERITY>
         </STATUS>
         <STMTRS>
            <CURDEF>BRL</CURDEF>
            <BANKACCTFROM>
               <BANKID>1</BANKID>
               <BRANCHID>1234-5</BRANCHID>
               <ACCTID>67890-X</ACCTID>
               <ACCTTYPE>CHECKING</ACCTTYPE>
            </BANKACCTFROM>
            <BANKTRANLIST>
               <DTSTART>20110331120000[-3:BRT]</DTSTART>
               <DTEND>20110430120000[-3:BRT]</DTEND>
               <STMTTRN>
                  <TRNTYPE>OTHER</TRNTYPE>
                  <DTPOSTED>20110401120000[-3:BRT]</DTPOSTED>
                  <TRNAMT>-35.65</TRNAMT>
                  <FITID>20110401135650</FITID>
                  <CHECKNUM>000000104485</CHECKNUM>
                  <REFNUM>104.485</REFNUM>
                  <MEMO>Compra com Cart\xe3o - 01/01 01:23 BURRITOS</MEMO>
               </STMTTRN>
            <LEDGERBAL>
               <BALAMT>48.52</BALAMT>
               <DTASOF>20110430120000[-3:BRT]</DTASOF>
            </LEDGERBAL>
         </STMTRS>
      </STMTTRNRS>
   </BANKMSGSRSV1>
</OFX>"""

OFX_DATA3 = """OFXHEADER:100
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
                <CODE>0
                <SEVERITY>INFO
            </STATUS>
            <DTSERVER>20110505174723[-3:GMT]
            <LANGUAGE>ENG
            <FI>
                <ORG>SANTANDER
                <FID>SANTANDER
            </FI>
        </SONRS>
    </SIGNONMSGSRSV1>
    <BANKMSGSRSV1>
        <STMTTRNRS>
            <TRNUID>1
            <STATUS>
                <CODE>0
                <SEVERITY>INFO
            </STATUS>
            <STMTRS>
                <CURDEF>BRC
                <BANKACCTFROM>
                    <BANKID>033
                    <ACCTID>012345678
                    <ACCTTYPE>CHECKING
                </BANKACCTFROM>
                <BANKTRANLIST>
                    <DTSTART>20110505174723[-3:GMT]
                    <DTEND>20110505174723[-3:GMT]
                    <STMTTRN>
                        <TRNTYPE>OTHER
                        <DTPOSTED>20110425000000[-3:GMT]
                        <TRNAMT>          -123.67
                        <FITID>00801000
                        <CHECKNUM>00801000
                        <PAYEEID>0
                        <MEMO>PGTO TITULO OUTRO
                    </STMTTRN>
                </BANKTRANLIST>
                <LEDGERBAL>
                    <BALAMT>            123.45
                    <DTASOF>20110505174723[-3:GMT]
                </LEDGERBAL>
            </STMTRS>
        </STMTTRNRS>
    </BANKMSGSRSV1>
</OFX>"""


class OFXImporterTest(DomainTest):
    def testOFXImportBBJurdica(self):
        ofx = OFXImporter()
        ofx.feed(StringIO(OFX_DATA))
        ofx.set_dry(True)
        ofx.process(self.trans)
        account = Account.select(connection=self.trans).orderBy('id')[-1]
        self.failUnless(account)
        self.assertEquals(account.description, "Bank - CHECKING")
        self.assertEquals(account.code, "1234")
        self.assertEquals(account.transactions.count(), 2)
        self.assertEquals(account.account_type, Account.TYPE_BANK)
        t1, t2 = sorted(account.transactions, key=operator.attrgetter('value'))
        self.assertEquals(t1.value, -5)
        self.assertEquals(t1.code, '90068259')
        self.assertEquals(t2.value, 50)
        self.assertEquals(t2.code, '90068258')

    def testOFXImportBBFisica(self):
        ofx = OFXImporter()
        ofx.feed(StringIO(OFX_DATA2))
        ofx.set_dry(True)
        ofx.process(self.trans)
        account = Account.select(connection=self.trans).orderBy('id')[-1]
        self.failUnless(account)
        self.assertEquals(account.description, "Banco do Brasil - CHECKING")
        self.assertEquals(account.code, "67890-X")
        self.assertEquals(account.transactions.count(), 1)
        self.assertEquals(account.account_type, Account.TYPE_BANK)
        t = account.transactions[0]
        self.assertEquals(t.value, Decimal("-35.65"))
        self.assertEquals(t.code, '000000104485')
        self.assertEquals(t.description,
                          'Compra com Cartão - 01/01 01:23 BURRITOS')

    def testOFXImportSantander(self):
        ofx = OFXImporter()
        ofx.feed(StringIO(OFX_DATA3))
        ofx.set_dry(True)
        ofx.process(self.trans)
        account = Account.select(connection=self.trans).orderBy('id')[-1]
        self.failUnless(account)
        self.assertEquals(account.description, "SANTANDER - CHECKING")
        self.assertEquals(account.code, "012345678")
        self.assertEquals(account.transactions.count(), 1)
        self.assertEquals(account.account_type, Account.TYPE_BANK)
        t = account.transactions[0]
        self.assertEquals(t.value, Decimal("-123.67"))
        self.assertEquals(t.code, '00801000')
        self.assertEquals(t.description,
                          'PGTO TITULO OUTRO')

#  LocalWords:  Compra
