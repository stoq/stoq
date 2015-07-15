# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Sales report implementation """

from stoqlib.database.runtime import get_default_store, get_current_branch
from stoqlib.domain.sale import Sale
from stoqlib.lib.formatters import (get_formatted_price,
                                    get_formatted_percentage,
                                    format_quantity)

from stoqlib.reporting.report import ObjectListReport, HTMLReport, TableReport
from stoqlib.lib.translation import stoqlib_gettext, stoqlib_ngettext

_ = stoqlib_gettext


class SaleOrderReport(HTMLReport):
    """Transfer Order receipt
        This class builds the namespace used in template
    """

    template_filename = 'sale/sale.html'
    title = _("Sale Order")
    complete_header = False

    def __init__(self, filename, order):
        self.order = order
        HTMLReport.__init__(self, filename)

    def _get_status_date(self, status):
        status_date = {Sale.STATUS_INITIAL: 'open_date',
                       Sale.STATUS_ORDERED: 'open_date',
                       Sale.STATUS_CONFIRMED: 'confirm_date',
                       Sale.STATUS_CANCELLED: 'cancel_date',
                       Sale.STATUS_QUOTE: 'open_date',
                       Sale.STATUS_RETURNED: 'return_date',
                       Sale.STATUS_RENEGOTIATED: 'close_date'}
        return getattr(self.order, status_date[status])

    def get_person_document(self):
        client = self.order.client
        if not client:
            return u''
        individual = client.person.individual
        if individual is not None:
            return individual.cpf
        company = client.person.company
        if company is not None:
            return company.cnpj

    def get_subtitle(self):
        return _(u'Number: %s - Sale %s on %s') % (
            self.order.identifier,
            Sale.get_status_name(self.order.status),
            self._get_status_date(self.order.status).strftime('%x'))

    def get_namespace(self):
        return {'status_quote': Sale.STATUS_QUOTE}


class SalesReport(ObjectListReport):
    title = _("Sales Report")
    main_object_name = (_("sale"), _("sales"))
    filter_format_string = _("with status <u>%s</u>")
    summary = ['total', 'total_quantity']


class ReturnedSalesReport(ObjectListReport):
    title = _("Returned Sales Report")


class ReturnedItemReport(ObjectListReport):
    title = _("Returned Items Report")


class SoldItemsByClientReport(ObjectListReport):
    title = _("Sales By Client Report")


class SoldItemsByBranchReport(ObjectListReport):
    """This report show a list of sold items by branch. For each item
    it show: product code, product description, branch name,
    sold quantity and total.
    """
    title = _("Sold Items by Branch Report")
    summary = ['quantity', 'total']
    template_filename = 'sale/sold_items_by_branch.html'

    def reset(self):
        ObjectListReport.reset(self)
        self.branch_total = {}
        self.branch_quantity = {}

    def accumulate(self, row):
        ObjectListReport.accumulate(self, row)
        # Total by Branch
        self.branch_total.setdefault(row.branch_name, 0)
        self.branch_quantity.setdefault(row.branch_name, 0)

        self.branch_total[row.branch_name] += row.total
        self.branch_quantity[row.branch_name] += row.quantity


class SalesPersonReport(TableReport):
    title = _("Sales")

    def __init__(self, filename, payments_list, salesperson,
                 *args, **kwargs):
        branch = get_current_branch(get_default_store()).get_description()
        self.payments_list = payments_list
        self._sales_person = salesperson
        if salesperson:
            salesperson_name = salesperson.get_description()
            singular = _("payment for {salesperson} on branch {branch}").format(
                salesperson=salesperson_name, branch=branch)
            plural = _("payments for {salesperson} on branch {branch}").format(
                salesperson=salesperson_name, branch=branch)
        else:
            singular = _("payment on branch %s") % branch
            plural = _("payments on branch %s") % branch

        self.main_object_name = (singular, plural)
        self.landscape = (salesperson is None)

        TableReport.__init__(self, filename, payments_list,
                             self.title, *args, **kwargs)

    def get_columns(self):
        columns = [dict(title=_("Sale #"), align='right'),
                   dict(title=_("Sale Total"), align='right'),
                   dict(title=_("Payment Value"), align='right'),
                   dict(title=_("Percentage"), align='right'),
                   dict(title=_("Commission Value"), align='right'),
                   dict(title=_("Items"), align='right')]
        if not self._sales_person:
            columns.insert(1, dict(title=_('Name')))
        return columns

    def get_row(self, obj):
        data = [unicode(obj.identifier),
                get_formatted_price(obj.total_amount),
                get_formatted_price(obj.payment_amount),
                get_formatted_percentage(obj.commission_percentage),
                get_formatted_price(obj.commission_value),
                format_quantity(obj.quantity_sold)]
        if not self._sales_person:
            data.insert(1, obj.salesperson_name)
        return data

    def reset(self):
        self._sales = set()
        self._total_amount = 0
        self._total_payment = 0
        self._total_percentage = 0
        self._total_value = 0
        self._total_sold = 0

    def accumulate(self, obj):
        # Count sale value only once
        if obj.id not in self._sales:
            if not obj.sale_returned:
                self._total_amount += obj.total_amount
            self._total_sold += obj.quantity_sold

        self._total_payment += obj.payment_amount
        self._total_value += obj.commission_value

        # payments_list might have multiples items that refers to the
        # same sale. This will count the right number of sales.
        self._sales.add(obj.id)

    def get_summary_row(self):
        total_sales = len(self._sales)
        if self._total_amount > 0:
            total_percentage = self._total_value * 100 / self._total_payment
            average_sale = self._total_amount / total_sales
        else:
            total_percentage = 0
            average_sale = 0

        sales_label = stoqlib_ngettext('%d sale', '%d sales',
                                       total_sales) % total_sales
        # TODO: Create a better way to add more lines to the summary row
        total_sales_label = get_formatted_price(self._total_amount)
        if self._sales_person:
            total_sales_label += ' (' + _("%s/sale") % (
                get_formatted_price(average_sale, )) + ')'

        summary_row = [sales_label,
                       total_sales_label,
                       get_formatted_price(self._total_payment),
                       get_formatted_percentage(total_percentage),
                       get_formatted_price(self._total_value),
                       format_quantity(self._total_sold)]
        if not self._sales_person:
            summary_row.insert(1, '')
        return summary_row


def test():  # pragma no cover
    from kiwi.ui.objectlist import ObjectList
    from stoqlib.api import api
    from stoq.gui.sales import SalesApp
    from stoqlib.domain.sale import SaleView
    api.prepare_test()
    store = api.new_store()

    class Foo(SalesApp):
        def __init__(self):
            pass

    a = Foo()
    ol = ObjectList(a.get_columns())
    data = store.find(SaleView)

    r = SalesReport('teste.pdf', ol, list(data))
    r.save_html('teste.html')
    r.save()

if __name__ == '__main__':  # pragma no cover
    test()
