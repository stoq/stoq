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

from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Person
from stoqlib.domain.product import Product
from stoqlib.domain.sale import Sale
from stoqlib.importers.csvimporter import CSVImporter
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SaleImporter(CSVImporter):
    fields = ['branch_name',
              'client_name',
              'salesperson_name',
              'payment_method',
              'product_list',  # ids separated by | or * for all
              'coupon_id',
              'open_date',
              'due_date']

    def process_one(self, data, fields, store):
        person = store.find(Person, name=data.branch_name).one()
        if person is None or person.branch is None:
            raise ValueError(u"%s is not a valid branch" % (
                data.branch_name, ))
        branch = person.branch

        person = store.find(Person, name=data.client_name).one()
        if person is None or person.client is None:
            raise ValueError(u"%s is not a valid client" % (
                data.client_name, ))
        client = person.client

        person = store.find(Person, name=data.salesperson_name).one()
        if person is None or person.sales_person is None:
            raise ValueError(u"%s is not a valid sales person" % (
                data.salesperson_name, ))
        salesperson = person.sales_person
        group = PaymentGroup(store=store)
        sale = Sale(client=client,
                    open_date=self.parse_date(data.open_date),
                    coupon_id=int(data.coupon_id),
                    invoice_number=int(data.coupon_id),
                    salesperson=salesperson,
                    branch=branch,
                    cfop_id=sysparam.get_object_id('DEFAULT_SALES_CFOP'),
                    group=group,
                    store=store)

        total_price = 0
        for product in self.parse_multi(Product, data.product_list, store):
            sale.add_sellable(product.sellable)
            total_price += product.sellable.price

        sale.order()
        method = PaymentMethod.get_by_name(store, data.payment_method)
        method.create_payment(Payment.TYPE_IN, group, branch, total_price,
                              self.parse_date(data.due_date))
        sale.confirm()
        # XXX: The payments are paid automatically when a sale is confirmed.
        #     So, we will change all the payment paid_date to the same date
        #     as open_date, then we can test the reports properly.
        for payment in sale.payments:
            if payment.is_paid():
                p = store.fetch(payment)
                p.paid_date = self.parse_date(data.open_date)
