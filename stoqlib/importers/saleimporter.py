# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime

from stoqlib.database.runtime import get_current_station
from stoqlib.domain.interfaces import IBranch, IClient, ISalesPerson
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.person import Person
from stoqlib.domain.product import Product
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import Till
from stoqlib.importers.csvimporter import CSVImporter
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SaleImporter(CSVImporter):
    fields = ['branch_name',
              'client_name',
              'salesperson_name',
              'payment_method',
              'product_list', # ids separated by | or * for all
              'coupon_id',
              'open_date',
              'due_date']

    def process_one(self, data, fields, trans):
        branch = IBranch(Person.selectOneBy(name=data.branch_name,
                                            connection=trans), None)
        if branch is None:
            raise ValueError("%s is not a valid branch" % (
                data.branch_name, ))
        client = IClient(Person.selectOneBy(name=data.client_name,
                                            connection=trans), None)
        if client is None:
            raise ValueError("%s is not a valid client" % (
                data.client_name, ))
        salesperson = ISalesPerson(
            Person.selectOneBy(name=data.salesperson_name,
                               connection=trans), None)
        if salesperson is None:
            raise ValueError("%s is not a valid salesperson" % (
                data.salesperson_name, ))
        group = PaymentGroup(connection=trans)
        sale = Sale(client=client,
                    open_date=self.parse_date(data.open_date),
                    coupon_id=int(data.coupon_id),
                    invoice_number=int(data.coupon_id),
                    salesperson=salesperson,
                    branch=branch,
                    cfop=sysparam(trans).DEFAULT_SALES_CFOP,
                    group=group,
                    connection=trans)

        total_price = 0
        for product in self.parse_multi(Product, data.product_list, trans):
            sale.add_sellable(product.sellable)
            total_price += product.sellable.price

        sale.order()
        method = PaymentMethod.get_by_name(trans, data.payment_method)
        method.create_inpayment(group, total_price,
                                self.parse_date(data.due_date))
        sale.confirm()
        #XXX: The payments are paid automatically when a sale is confirmed.
        #     So, we will change all the payment paid_date to the same date
        #     as open_date, then we can test the reports properly.
        for payment in sale.group.payments:
            if payment.is_paid():
                p = trans.get(payment)
                p.paid_date = self.parse_date(data.open_date)

    def before_start(self, trans):
        till = Till.get_current(trans)
        if till is None:
            till = Till(connection=trans,
                        station=get_current_station(trans))
            till.open_till()
            assert till == Till.get_current(trans)

    def when_done(self, trans):
        # This is sort of hack, set the opening/closing dates to the date before
        # it's run, so we can open/close the till in the tests, which uses
        # the examples.
        till = Till.get_current(trans)
        # Do not leave anything in the till.
        till.add_debit_entry(till.get_balance(),
                             _(u'Amount removed from Till on %s' %
                               till.opening_date.strftime('%x')))
        till.close_till()
        yesterday = datetime.date.today() - datetime.timedelta(1)
        till.opening_date = yesterday
        till.closing_date = yesterday
