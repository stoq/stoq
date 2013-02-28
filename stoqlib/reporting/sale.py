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
from stoqlib.domain.views import SoldItemsByBranchView
from stoqlib.reporting.base.tables import ObjectTableColumn as OTC
from stoqlib.lib.formatters import (get_formatted_price,
                                    get_formatted_percentage,
                                    format_quantity)

from stoqlib.reporting.report import ObjectListReport, HTMLReport
from stoqlib.reporting.template import SearchResultsReport, OldObjectListReport
from stoqlib.lib.translation import stoqlib_gettext

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
                       Sale.STATUS_PAID: 'close_date',
                       Sale.STATUS_CANCELLED: 'cancel_date',
                       Sale.STATUS_QUOTE: 'open_date',
                       Sale.STATUS_RETURNED: 'return_date',
                       Sale.STATUS_RENEGOTIATED: 'close_date'}
        return getattr(self.order, status_date[status])

    #
    # BaseReportTemplate hooks
    #

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
                    self.order.get_order_number_str(),
                    Sale.get_status_name(self.order.status),
                    self._get_status_date(self.order.status).strftime('%x'))


class SalesReport(ObjectListReport):
    title = _("Sales Report")
    main_object_name = (_("sale"), _("sales"))
    filter_format_string = _("with status <u>%s</u>")
    summary = ['total', 'total_quantity']


class SoldItemsByBranchReport(OldObjectListReport):
    """This report show a list of sold items by branch. For each item
    it show: product code, product description, branch name,
    sold quantity and total.
    """
    obj_type = SoldItemsByBranchView
    report_name = _("Sold Items by Branch Report")

    def __init__(self, filename, objectlist, items, *args, **kwargs):
        self._items = items
        ObjectListReport.__init__(self, filename, objectlist, items,
                                  SoldItemsByBranchReport.report_name,
                                  landscape=True,
                                  *args, **kwargs)
        self.setup_tables()

    def setup_tables(self):
        self.total = 0
        self.quantity = 0

        self.branch_total = {}
        self.branch_quantity = {}

        for i in self._items:
            # Sold Items
            self.total += i.total
            self.quantity += i.quantity

            # Total by Branch
            self.branch_total.setdefault(i.branch_name, 0)
            self.branch_quantity.setdefault(i.branch_name, 0)

            self.branch_total[i.branch_name] += i.total
            self.branch_quantity[i.branch_name] += i.quantity

        self._setup_items_table()

        # Only show branch table if have more than one branch
        if len(self.branch_total) > 1:
            self._setup_branch_table()

    def _setup_items_table(self):
        self.add_summary_by_column(_(u'Quantity'), format_quantity(self.quantity))
        self.add_summary_by_column(_(u'Total'), get_formatted_price(self.total))
        self.add_blank_space(10)
        self.add_paragraph(_('Total Sold'), style='Normal-Bold')
        self.add_object_table(self._items, self.get_columns(),
                              summary_row=self.get_summary_row())

    def _setup_branch_table(self):
        branches_columns = [OTC(_("Branch"), lambda obj: obj),
                            OTC(_("Total quantity"), lambda obj:
                                  format_quantity(self.branch_quantity[obj])),
                            OTC(_("Total"), lambda obj:
                                  get_formatted_price(self.branch_total[obj]))]
        self.add_blank_space(10)
        self.add_paragraph(_(u'Totals by Branch'), style='Normal-Bold')
        self.add_object_table(self.branch_total, branches_columns)


class SalesPersonReport(SearchResultsReport):
    report_name = _("Sales")

    def __init__(self, filename, payments_list, salesperson_name,
                 *args, **kwargs):
        branch = get_current_branch(get_default_store()).get_description()
        self.payments_list = payments_list
        if salesperson_name:
            singular = _("payment for {salesperson} on branch {branch}").format(
                         salesperson=salesperson_name, branch=branch)
            plural = _("payments for {salesperson} on branch {branch}").format(
                       salesperson=salesperson_name, branch=branch)
        else:
            singular = _("payment on branch %s") % branch
            plural = _("payments on branch %s") % branch

        self.main_object_name = (singular, plural)

        SearchResultsReport.__init__(self, filename, payments_list,
                                     SalesPersonReport.report_name,
                                     landscape=(salesperson_name is None),
                                     *args, **kwargs)
        self._sales_person = salesperson_name
        self._setup_sales_person_table()

    def _get_columns(self):
        columns = [OTC(_("Sale"), lambda obj: obj.identifier, width=80)]
        if self._sales_person is None:
            columns.append(OTC(_("Name"), lambda obj: obj.salesperson_name,
                           expand=True, truncate=True))

        columns.extend([
            OTC(_("Sale Total"), lambda obj: get_formatted_price(
                obj.get_total_amount()), truncate=True, width=105),
            OTC(_("Payment Value"), lambda obj: get_formatted_price(
                obj.get_payment_amount()), truncate=True, width=190),
            OTC(_("Percentage"), lambda obj: get_formatted_percentage(
                obj.commission_percentage), truncate=True,
                width=100),
            OTC(_("Commission Value"), lambda obj: get_formatted_price(
                obj.commission_value), truncate=True, width=180),
            OTC(_("Items"), lambda obj: format_quantity(obj.quantity_sold()),
                width=45, truncate=True)])
        return columns

    def _setup_sales_person_table(self):
        total_amount = total_payment = total_percentage = total_value = \
            total_sold = 0

        sales = {}
        for commission_view in self.payments_list:
            # Count sale value only once
            if commission_view.id not in sales:
                total_amount += commission_view.get_total_amount()
                total_sold += commission_view.quantity_sold()
            if commission_view.sale_returned():
                total_amount -= commission_view.get_total_amount()

            total_payment += commission_view.get_payment_amount()
            total_value += commission_view.commission_value
            sales[commission_view.id] = 1

        if total_amount > 0:
            total_percentage = total_value * 100 / total_payment
        else:
            total_percentage = 0

        summary_row = ["", _("Total:"), get_formatted_price(total_amount),
                       get_formatted_price(total_payment),
                       get_formatted_percentage(total_percentage),
                       get_formatted_price(total_value),
                       format_quantity(total_sold), '']

        # payments_list might have multiples items that refers to the
        # same sale. This will count the right number of sales.
        sales_qty = len(sales)

        text = None
        if self._sales_person is not None:
            summary_row.pop(0)
            va = 0
            if total_amount:
                va = total_amount / sales_qty
            text = _("Sold value per sales %s") % (get_formatted_price(va, ))

        self.add_object_table(self.payments_list, self._get_columns(),
                              summary_row=summary_row)

        if text:
            self.add_preformatted_text(text)
            self.add_preformatted_text(_("Total of sales: %d") % sales_qty)


def test():
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

if __name__ == '__main__':
    test()
