# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
from decimal import Decimal
import mock
import os
import tempfile

import unittest

from stoqlib.api import api
from stoqlib.lib.boleto import (
    BankSantander, BankBanrisul, BankBB, BankBradesco, custom_property,
    BankCaixa, BankItau, BankReal, BoletoException, BankInfo, BILL_OPTION_CUSTOM)
from stoqlib.domain.account import BankAccount, BillOption
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.diffutils import diff_pdf_htmls
from stoqlib.lib.pdf import pdftohtml
from stoqlib.reporting.boleto import BillReport
from stoqlib.lib.unittestutils import get_tests_datadir


class TestBillReport(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        self._filename = tempfile.mktemp(prefix="stoqlib-test-boleto-",
                                         suffix=".pdf")
        self._pdf_html = None

    def tearDown(self):
        DomainTest.tearDown(self)
        try:
            os.unlink(self._filename)
        except OSError:
            pass
        if self._pdf_html:
            try:
                os.unlink(self._pdf_html)
            except OSError:
                pass

    def _configure_boleto(self, number, account, agency, **kwargs):
        bill = PaymentMethod.get_by_name(self.store, u'bill')
        bank_account = BankAccount(account=bill.destination_account,
                                   bank_account=account,
                                   bank_branch=agency,
                                   bank_number=int(number),
                                   store=self.store)

        for key, value in kwargs.items():
            BillOption(store=self.store,
                       bank_account=bank_account,
                       option=unicode(key),
                       value=value)
        api.sysparam.set_string(self.store, 'BILL_INSTRUCTIONS',
                                u'Primeia linha da instrução')

    def _get_expected(self, filename, generated):
        fname = get_tests_datadir(filename + '.pdf.html')
        if not os.path.exists(fname):
            open(fname, 'w').write(open(generated).read())
        return fname

    def _create_bill_sale(self, installments=1):
        sale = self.create_sale()
        sale.identifier = 123
        self.add_product(sale)
        sale.order()
        payments = self.add_payments(sale, method_type=u'bill',
                                     date=datetime.datetime(2011, 5, 30),
                                     installments=installments)
        for i, payment in enumerate(payments, 400):
            payment.identifier = i
        sale.client = self.create_client()
        address = self.create_address()
        address.person = sale.client.person
        sale.confirm()
        return sale

    @mock.patch('stoqlib.lib.boleto.localtoday')
    def _render_bill_to_html(self, sale, localtoday):
        localtoday.return_value = datetime.date(2011, 05, 30)
        report = BillReport(self._filename, list(sale.payments))
        report.add_payments()
        report.save()
        self._pdf_html = tempfile.mktemp(prefix="stoqlib-test-boleto-",
                                         suffix=".pdf.html")
        pdftohtml(self._filename, self._pdf_html)
        return self._pdf_html

    def _diff(self, sale, name):
        generated = self._render_bill_to_html(sale)
        expected = self._get_expected(name, generated)
        diff = diff_pdf_htmls(expected, generated)
        self.failIf(diff, '%s\n%s' % ("Files differ, output:", diff))

    def test_banco_do_brasil(self):
        sale = self._create_bill_sale()
        self._configure_boleto(u"001",
                               convenio=u"12345678",
                               agency=u"1172",
                               account=u"00403005",
                               especie_documento=u"DM")
        self._diff(sale, 'boleto-001')

    def test_banco_do_brasil_com_d_v(self):
        sale = self._create_bill_sale()
        self._configure_boleto(u"001",
                               convenio=u"12345678",
                               agency=u"1172-X",
                               account=u"00403005-X",
                               especie_documento=u"DM")
        self._diff(sale, 'boleto-001')

    def test_nossa_caixa(self):
        sale = self._create_bill_sale()
        self._configure_boleto(u"104",
                               agency=u"1565",
                               account=u"414-3",
                               especie_documento=u"DM",
                               carteira=u'')

        self._diff(sale, 'boleto-104')

    def test_itau(self):
        sale = self._create_bill_sale()
        self._configure_boleto(u"341",
                               account=u"13877",
                               agency=u"1565",
                               carteira=u'175',
                               especie_documento=u"DM")

        self._diff(sale, 'boleto-341')

    def test_bradesco(self):
        sale = self._create_bill_sale()
        self._configure_boleto(u"237",
                               account=u"029232-4",
                               agency=u"278-0",
                               carteira=u'06',
                               especie_documento=u"DM")

        self._diff(sale, 'boleto-237')

    def test_real(self):
        sale = self._create_bill_sale()
        self._configure_boleto(u"356",
                               account=u"5705853",
                               agency=u"0531",
                               carteira=u'06',
                               especie_documento=u"DM")

        self._diff(sale, 'boleto-356')

    def test_carne(self):
        sale = self._create_bill_sale(installments=2)
        self._configure_boleto(u"001",
                               account=u"5705853",
                               agency=u"0531",
                               carteira=u'06',
                               especie_documento=u"DM")

        self._diff(sale, 'boleto-001-carne')


class TestBank(BankInfo):
    description = 'Test Bank'
    bank_number = 99
    foo = custom_property('foo', 8)

    campo_livre = '0' * 25

    options = dict(
        opcao_teste=BILL_OPTION_CUSTOM,
        segunda_opcao=BILL_OPTION_CUSTOM,
    )


class TestBankInfo(DomainTest):

    def setUp(self):
        self.bank = self.create_bank_account(bank_branch=u'1102',
                                             bank_account=u'9000150',)
        payment = self.create_payment(value=Decimal('550'),
                                      date=datetime.date(2000, 7, 4))
        payment.identifier = 134
        payment.method.destination_account.bank = self.bank
        self.info = TestBank(payment)

    def test_custom_property(self):
        with self.assertRaises(BoletoException):
            self.info.foo = '123-2-3'

    def test_instrucoes(self):
        inst = (u'Primeia linha da instrução\n$DATE\n$PENALTY foo $INTEREST\n'
                ' $DISCOUNT e $INVOICE_NUMBER')
        with self.sysparam(BILL_INSTRUCTIONS=inst,
                           BILL_PENALTY=Decimal(11),
                           BILL_INTEREST=Decimal('0.4'),
                           BILL_DISCOUNT=Decimal('123.45')):
            self.assertEquals(self.info.instrucoes,
                              [u'Primeia linha da instru\xe7\xe3o',
                               u'04/07/2000',
                               u'$60.50 foo $2.20',
                               u' $678.98 e 00134'])

    def test_barcode(self):
        self.assertEquals(len(self.info.barcode), 44)
        with self.assertRaises(BoletoException):
            self.info.campo_livre = '0' * 27
            self.info.barcode

    def test_formata_numero(self):
        with self.assertRaises(BoletoException):
            TestBank.formata_numero('123456', 3)

        self.assertEquals(TestBank.formata_numero('123', 6), '000123')

    def test_dv_agencia(self):
        self.info.agencia = '123-4'
        self.assertEquals(self.info.dv_agencia, '4')

        self.info.agencia = '1'
        self.assertEquals(self.info.dv_agencia, '')

    def test_dv_conta(self):
        self.info.conta = '123-9'
        self.assertEquals(self.info.dv_conta, '9')

        self.info.conta = '1'
        self.assertEquals(self.info.dv_conta, '')

    def test_get_extra_options(self):
        self.assertEquals(BankInfo.get_extra_options(), [])
        self.assertEquals(TestBank.get_extra_options(), ['opcao_teste',
                                                         'segunda_opcao'])

    def test_validate_field(self):
        with self.assertRaisesRegexp(BoletoException, 'The field cannot have spaces'):
            TestBank.validate_field('with spaces')

        with self.assertRaisesRegexp(BoletoException,
                                     'The field cannot have dots of commas'):
            TestBank.validate_field('cant,have,commas')

        with self.assertRaisesRegexp(BoletoException,
                                     'The field cannot have dots of commas'):
            TestBank.validate_field('cant.have.dots')

        with self.assertRaisesRegexp(BoletoException, 'More than one hyphen found'):
            TestBank.validate_field('only-one-hyphen-allowed')

        with self.assertRaisesRegexp(BoletoException, 'Verifier digit cannot be empty'):
            TestBank.validate_field('noverifiierdigit-')

        with self.assertRaisesRegexp(BoletoException, 'Account needs to be a number'):
            TestBank.validate_field('foobar')

        TestBank.validate_field_dv = '0'
        TestBank.validate_field_func = 'modulo11'
        with self.assertRaisesRegexp(BoletoException, 'Invalid verifier digit'):
            TestBank.validate_field('1234-5')
        with self.assertRaisesRegexp(BoletoException,
                                     'Verifier digit must be a number or 0'):
            TestBank.validate_field('1234-y')

        # Now a valid dv
        TestBank.validate_field('1234-3')

        TestBank.validate_field_func = 'modulo10'
        with self.assertRaisesRegexp(BoletoException, 'Invalid verifier digit'):
            TestBank.validate_field('1234-5')

        # Now a valid dv for modulo 11
        TestBank.validate_field('1234-4')

        # Now with an X verifier digit
        TestBank.validate_field_dv = 'x'
        TestBank.validate_field_func = 'modulo11'
        with self.assertRaisesRegexp(BoletoException, 'Invalid verifier digit'):
            TestBank.validate_field('1234-x')
        TestBank.validate_field('0295-X')

        # Without a func, all digits are valid
        TestBank.validate_field_func = None
        TestBank.validate_field('0295-1')
        TestBank.validate_field('0295-2')


class TestBancoBanrisul(DomainTest):
    def setUp(self):
        payment = self.create_payment(value=Decimal('550'),
                                      date=datetime.date(2000, 7, 4))
        bank = self.create_bank_account(bank_branch=u'1102',
                                        bank_account=u'9000150',)
        bank.add_bill_option(u'especie_documento', u'DM')
        bank.add_bill_option(u'nosso_numero', u'22832563')
        payment.method.destination_account.bank = bank
        self.dados = BankBanrisul(payment)

    def test_linha_digitavel(self):
        self.assertEqual(
            self.dados.linha_digitavel,
            '04192.11107 29000.150226 83256.340593 8 10010000055000'
        )

    def test_tamanho_codigo_de_barras(self):
        self.assertEqual(len(self.dados.barcode), 44)

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
                         '04198100100000550002111029000150228325634059')

    def test_campo_livre(self):
        self.assertEqual(self.dados.campo_livre,
                         '2111029000150228325634059')

    def test_validate_field(self):
        valid = ['06.181631.0-9.',
                 '06.011.348.0-8'
                 ]
        for _ in valid:
            pass


class TestBB(DomainTest):
    def setUp(self):
        payment = self.create_payment(value=Decimal('2952.95'),
                                      date=datetime.date(2011, 3, 8))
        bank = self.create_bank_account(bank_branch=u'9999',
                                        bank_account=u'99999',)
        bank.add_bill_option(u'especie_documento', u'DM')
        bank.add_bill_option(u'convenio', u'7777777')
        bank.add_bill_option(u'nosso_numero', u'87654')
        payment.method.destination_account.bank = bank
        self.dados = BankBB(payment)

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
                         '00190.00009 07777.777009 00087.654182 6 49000000295295'
                         )

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
                         '00196490000002952950000007777777000008765418'
                         )

    def test_validate_field(self):
        valid = ['0295-x',
                 '2589-5',
                 '3062-7',
                 '8041-1',
                 '15705-8',
                 '39092-5',
                 '83773-3']
        for v in valid:
            self.dados.validate_field(v)


class TestBancoBradesco(DomainTest):
    def setUp(self):
        payment = self.create_payment(value=Decimal('8280'),
                                      date=datetime.date(2011, 2, 5))
        bank = self.create_bank_account(bank_branch=u'278-0',
                                        bank_account=u'039232-4',)
        bank.add_bill_option(u'especie_documento', u'DM')
        bank.add_bill_option(u'carteira', u'06')
        bank.add_bill_option(u'nosso_numero', u'2125525')
        payment.method.destination_account.bank = bank
        self.dados = BankBradesco(payment)

        payment = self.create_payment(value=Decimal('2952.95'),
                                      date=datetime.date(2011, 3, 9))
        bank = self.create_bank_account(bank_branch=u'1172',
                                        bank_account=u'403005',)
        bank.add_bill_option(u'especie_documento', u'DM')
        bank.add_bill_option(u'carteira', u'06')
        bank.add_bill_option(u'nosso_numero', u'75896452')
        account = self.create_account()
        account.bank = bank
        payment.method.destination_account = account
        self.dados2 = BankBradesco(payment)

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
                         '23790.27804 60000.212559 25003.923205 4 48690000828000'
                         )

        self.assertEqual(self.dados2.linha_digitavel,
                         '23791.17209 60007.589645 52040.300502 1 49010000295295'
                         )

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
                         '23794486900008280000278060000212552500392320'
                         )
        self.assertEqual(self.dados2.barcode,
                         '23791490100002952951172060007589645204030050'
                         )

    def test_agencia(self):
        self.assertEqual(self.dados.agencia, '0278-0')

    def test_conta(self):
        self.assertEqual(self.dados.conta, '0039232-4')

    def test_validate_field(self):
        valid = ['0278-0',
                 '1172',
                 '14978-0',
                 '403005',
                 '0039232-4',
                 '02752']
        for v in valid:
            self.dados.validate_field(v)

    def test_dv_nosso_numero(self):
        self.dados.nosso_numero = '1236'
        self.assertEquals(self.dados.dv_nosso_numero, 'P')

        self.dados.nosso_numero = '1244'
        self.assertEquals(self.dados.dv_nosso_numero, 0)

    def test_carteira(self):
        payment = self.create_payment(value=Decimal('2952.95'),
                                      date=datetime.date(2011, 3, 9))
        bank = self.create_bank_account(bank_branch=u'02752',
                                        bank_account=u'14978-0',)
        bank.add_bill_option(u'especie_documento', u'DM')
        bank.add_bill_option(u'carteira', u'9')
        bank.add_bill_option(u'nosso_numero', u'75896452')
        account = self.create_account()
        account.bank = bank
        payment.method.destination_account = account
        x = BankBradesco(payment)
        self.assertEquals(
            x.barcode, '23793490100002952952752090007589645200149780')

        x.validate_option(u'carteira', '9')
        x.validate_option(u'carteira', '09')
        self.assertRaises(BoletoException, x.validate_option, u'carteira', '')
        self.assertRaises(BoletoException, x.validate_option, u'carteira', 'CNR')
        self.assertRaises(BoletoException, x.validate_option, u'carteira', '-1')
        self.assertRaises(BoletoException, x.validate_option, u'carteira', '100')


class TestBancoCaixa(DomainTest):
    def setUp(self):
        payment = self.create_payment(value=Decimal('355'),
                                      date=datetime.date(2011, 2, 5))
        bank = self.create_bank_account(bank_branch=u'1565',
                                        bank_account=u'414-3')
        bank.add_bill_option(u'especie_documento', u'DM')
        bank.add_bill_option(u'carteira', u'SR')
        bank.add_bill_option(u'nosso_numero', u'19525086')
        payment.method.destination_account.bank = bank
        self.dados = BankCaixa(payment)

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
                         '10498.01952 25086.156509 00000.004143 7 48690000035500'
                         )

    def test_tamanho_codigo_de_barras(self):
        self.assertEqual(len(self.dados.barcode), 44)

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
                         '10497486900000355008019525086156500000000414'
                         )


class TestBancoItau(DomainTest):
    def setUp(self):
        payment = self.create_payment(value=Decimal('123.45'),
                                      date=datetime.date(2002, 5, 1))
        bank = self.create_bank_account(bank_branch=u'0057',
                                        bank_account=u'12345-7')
        bank.add_bill_option(u'especie_documento', u'DM')
        bank.add_bill_option(u'carteira', u'110')
        bank.add_bill_option(u'nosso_numero', u'12345678')
        payment.method.destination_account.bank = bank
        self.dados = BankItau(payment)

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
                         '34191.10121 34567.880058 71234.570001 6 16670000012345'
                         )

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
                         '34196166700000123451101234567880057123457000'
                         )


class TestBancoReal(DomainTest):
    def setUp(self):
        payment = self.create_payment(value=Decimal('355'),
                                      date=datetime.date(2011, 2, 5))
        bank = self.create_bank_account(bank_branch=u'0531',
                                        bank_account=u'5705853',)
        bank.add_bill_option(u'especie_documento', u'DM')
        bank.add_bill_option(u'carteira', u'06')
        bank.add_bill_option(u'nosso_numero', u'123')
        payment.method.destination_account.bank = bank

        self.dados = BankReal(payment)

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
                         '35690.53154 70585.390001 00000.001230 8 48690000035500'
                         )

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
                         '35698486900000355000531570585390000000000123'
                         )


class TestSantander(DomainTest):
    def setUp(self):
        payment = self.create_payment(value=Decimal('2952.95'),
                                      date=datetime.date(2012, 1, 22))
        bank = self.create_bank_account(bank_branch=u'1333',
                                        bank_account=u'0707077',)
        bank.add_bill_option(u'especie_documento', u'DM')
        bank.add_bill_option(u'nosso_numero', u'1234567')
        payment.method.destination_account.bank = bank

        self.dados = BankSantander(payment)

    def test_linha_digitavel(self):
        self.assertEqual(self.dados.linha_digitavel,
                         '03399.07073 07700.000123 34567.901029 6 52200000295295'
                         )

    def test_tamanho_codigo_de_barras(self):
        self.assertEqual(len(self.dados.barcode), 44)

    def test_codigo_de_barras(self):
        self.assertEqual(self.dados.barcode,
                         '03396522000002952959070707700000123456790102'
                         )

if __name__ == '__main__':
    unittest.main()
