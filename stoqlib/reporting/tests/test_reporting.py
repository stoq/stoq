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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Fabio Morbec      <fabio@async.com.br>
##
""" This module test reporties """
import datetime
import os
import sys

import stoqlib

from stoqlib.domain.payment.views import InPaymentView, OutPaymentView
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.views import ProductFullStockView
from stoqlib.reporting.payment import (ReceivablePaymentReport,
                                       PayablePaymentReport)
from stoqlib.reporting.product import ProductReport
from stoqlib.lib.diffutils import diff_files

class TestReport(DomainTest):
    def checkPDF(self, report_class, *args, **kwargs):
        exists_pdf = False
        frame = sys._getframe(1)
        filename = "%s.pdf" % (frame.f_code.co_name[4:],)
        filename = os.path.join(os.path.dirname(stoqlib.__file__),
                               "reporting", "tests", "data", filename)
        if os.path.exists(filename):
            original_filename = filename
            exists_pdf = True
            filename = filename + '.tmp'
        report = report_class(filename, *args, **kwargs)
        report.save()

        if exists_pdf:
            path = os.path.split(filename)[0]
            olddir = os.getcwd()
            os.chdir(path)

            for name in (original_filename, filename):
                cmd = 'pdftohtml -noframes -i -q %s %s.html' % (name, name)
                os.system(cmd)
            try:
                self._comparePDF(original_filename, filename)
            finally:
                os.chdir(olddir)

        if filename.endswith('.tmp'):
            os.unlink(filename)

    def _comparePDF(self, original_filename, filename):
        original_filename_html = "%s.html" % (original_filename,)
        tmp_html = "%s.html" % (filename,)

        out_original_filename = "%s.htm" % (original_filename,)
        out_tmp = "%s.htm" % (filename,)

        input_original = open(original_filename_html)
        input_filename = open(tmp_html)
        output_original = open(out_original_filename, "w")
        output_tmp = open(out_tmp, "w")

        for line in input_original:
            if line.startswith("<META"):
                continue
            output_original.write(line,)
        for line in input_filename:
            if line.startswith("<META"):
                continue
            output_tmp.write(line,)
        for file in (input_original, input_filename, output_original,
                     output_tmp):
            file.close()
        retval = diff_files(out_original_filename, out_tmp)
        os.unlink(tmp_html)
        os.unlink(out_tmp)
        os.unlink(out_original_filename)
        os.unlink(original_filename_html)
        if retval:
            if filename.endswith('.tmp'):
                os.unlink(filename)
            raise AssertionError("Files differ, check output above")

    def testPayablePaymentReport(self):
        out_payments = list(OutPaymentView.select(connection=self.trans))
        for item in out_payments:
            item.payment.due_date = datetime.date(2007, 1, 1)
        self.checkPDF(PayablePaymentReport, out_payments, date=datetime.date(2007, 1, 1))

    def testReceivablePaymentReport(self):
        in_payments = list(InPaymentView.select(connection=self.trans))
        for item in in_payments:
            item.due_date = datetime.date(2007, 1, 1)
        self.checkPDF(ReceivablePaymentReport, in_payments, date=datetime.date(2007, 1, 1))

    def testTransferOrderReceipt(self):
        from stoqlib.domain.transfer import TransferOrder, TransferOrderItem
        from stoqlib.reporting.transfer_receipt import TransferOrderReceipt
        orders = list(TransferOrder.select(connection=self.trans))
        items = TransferOrderItem.selectBy(transfer_order=orders[0],
                                           connection=self.trans)
        self.checkPDF(TransferOrderReceipt, orders[0], items)

    def testProductReport(self):
        products = list(ProductFullStockView.select(connection=self.trans))
        branch = self.create_branch()
        self.checkPDF(ProductReport, products,
                      branch=branch,
                      date=datetime.date(2007, 1, 1))
