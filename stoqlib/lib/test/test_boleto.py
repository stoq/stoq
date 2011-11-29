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

from ConfigParser import SafeConfigParser
import datetime
import os
import StringIO
import tempfile

from kiwi.component import provide_utility

import stoqlib
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.boleto import BillReport
from stoqlib.lib.diffutils import diff_pdf_htmls
from stoqlib.lib.interfaces import IStoqConfig
from stoqlib.lib.pdf import pdftohtml

class MockConfig:
    def __init__(self, fp):
        self._config = SafeConfigParser()
        self._config.readfp(fp)

    def get(self, section, option):
        if not self._config.has_section(section):
            return

        if not self._config.has_option(section, option):
            return

        return self._config.get(section, option)

    def items(self, section):
        if not self._config.has_section(section):
            return {}
        return self._config.items(section)

class TestBoleto(DomainTest):
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

    def _configure_boleto(self, bank, **kwargs):
        tmpl = """[Boleto]
banco = %s
instrucao1 = Primeia linha da instrução
[%s]
""" % (bank, bank)
        for key, value in kwargs.items():
            tmpl += '%s = %s\n' % (key, value)
        fp = StringIO.StringIO(tmpl)
        config = MockConfig(fp)
        provide_utility(IStoqConfig, config, replace=True)

    def _get_expected(self, filename, generated):
        fname = os.path.join(os.path.dirname(stoqlib.__file__),
                            "lib", "test", filename + '.pdf.html')
        if not os.path.exists(fname):
            open(fname, 'w').write(open(generated).read())
        return fname

    def _create_bill_sale(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        self.add_payments(sale, method_type='bill',
                          date=datetime.date(2011, 5, 30))
        sale.client = self.create_client()
        address = self.create_address()
        address.person = sale.client.person
        sale.confirm()
        return sale

    def _render_bill_to_html(self, sale):
        report = BillReport(self._filename, list(sale.payments))
        report.today = datetime.date(2011, 05, 30)
        report.add_payments()
        report.override_payment_id(400)
        report.override_payment_description(['sale XXX', 'XXX - description'])
        report.save()
        self._pdf_html = tempfile.mktemp(prefix="stoqlib-test-boleto-",
                                         suffix=".pdf.html")
        pdftohtml(self._filename, self._pdf_html)
        return self._pdf_html

    def _diff(self, sale, name):
        generated = self._render_bill_to_html(sale)
        expected = self._get_expected(name, generated)
        if diff_pdf_htmls(expected, generated):
            raise AssertionError("files differ, see output above")

    def testBancoDoBrasil(self):
        sale = self._create_bill_sale()
        self._configure_boleto("001",
                               convenio="12345678",
                               len_convenio="8",
                               agencia="1172",
                               conta="00403005")

        self._diff(sale, 'boleto-001')

    def testNossaCaixa(self):
        sale = self._create_bill_sale()
        self._configure_boleto("104",
                               agencia="1565",
                               conta="414-3")

        self._diff(sale, 'boleto-104')

    def testItau(self):
        sale = self._create_bill_sale()
        self._configure_boleto("341",
                               conta="13877",
                               agencia="1565",
                               carteira='175')

        self._diff(sale, 'boleto-341')

    def testBradesco(self):
        sale = self._create_bill_sale()
        self._configure_boleto("237",
                               conta="029232-4",
                               agencia="278-0",
                               carteira='06')

        self._diff(sale, 'boleto-237')

    def testReal(self):
        sale = self._create_bill_sale()
        self._configure_boleto("356",
                               conta="5705853",
                               agencia="0531",
                               carteira='06')

        self._diff(sale, 'boleto-356')
