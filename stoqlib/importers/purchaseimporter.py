# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source
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

from stoqlib.database.runtime import get_current_user
from stoqlib.domain.person import Person
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.domain.receiving import ReceivingOrder, ReceivingOrderItem
from stoqlib.domain.sellable import Sellable
from stoqlib.importers.csvimporter import CSVImporter


class PurchaseImporter(CSVImporter):
    fields = ['supplier_name',
              'transporter_name',
              'branch_name',
              'user_name',
              'payment_method',
              'due_date',
              'sellable_list',  # ids separated by | or * for all
              'invoice',
              'quantity']

    def process_one(self, data, fields, store):
        person = store.find(Person, name=data.supplier_name).one()
        if person is None or person.supplier is None:
            raise ValueError(u"%s is not a valid supplier" % (
                data.supplier_name, ))
        supplier = person.supplier

        person = store.find(Person, name=data.transporter_name).one()
        if person is None or person.transporter is None:
            raise ValueError(u"%s is not a valid transporter" % (
                data.transporter_name, ))
        transporter = person.transporter

        person = store.find(Person, name=data.branch_name).one()
        if person is None or person.branch is None:
            raise ValueError(u"%s is not a valid branch" % (
                data.branch_name, ))
        branch = person.branch

        person = store.find(Person, name=data.user_name).one()
        if person is None or person.login_user is None:
            raise ValueError(u"%s is not a valid user" % (
                data.user_name, ))
        login_user = person.login_user

        group = PaymentGroup(store=store)
        purchase = PurchaseOrder(store=store,
                                 status=PurchaseOrder.ORDER_PENDING,
                                 supplier=supplier,
                                 transporter=transporter,
                                 group=group,
                                 responsible=get_current_user(store),
                                 branch=branch)

        for sellable in self.parse_multi(Sellable, data.sellable_list, store):
            if not sellable.product:
                continue
            PurchaseItem(store=store,
                         quantity=int(data.quantity),
                         base_cost=sellable.cost,
                         sellable=sellable,
                         order=purchase)

        method = PaymentMethod.get_by_name(store, data.payment_method)
        method.create_payment(Payment.TYPE_OUT, purchase.group, branch,
                              purchase.purchase_total,
                              self.parse_date(data.due_date))
        purchase.confirm()

        receiving_order = ReceivingOrder(responsible=login_user,
                                         supplier=supplier,
                                         invoice_number=int(data.invoice),
                                         transporter=transporter,
                                         branch=branch,
                                         store=store)
        receiving_order.add_purchase(purchase)

        for purchase_item in purchase.get_items():
            ReceivingOrderItem(
                store=store,
                cost=purchase_item.sellable.cost,
                sellable=purchase_item.sellable,
                quantity=int(data.quantity),
                purchase_item=purchase_item,
                receiving_order=receiving_order
            )
        receiving_order.confirm()
