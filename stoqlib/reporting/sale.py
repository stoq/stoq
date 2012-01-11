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

from kiwi.datatypes import currency

from stoqlib.database.runtime import get_connection, get_current_branch
from stoqlib.domain.commission import CommissionView
from stoqlib.domain.interfaces import ICompany, IIndividual
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.domain.views import SoldItemsByBranchView
from stoqlib.reporting.base.default_style import TABLE_LINE_BLANK
from stoqlib.reporting.base.tables import (ObjectTableColumn as OTC,
                                           TableColumn as TC, HIGHLIGHT_NEVER)
from stoqlib.reporting.base.flowables import RIGHT
from stoqlib.lib.formatters import (get_formatted_price,
                                   get_formatted_percentage,
                                   format_quantity,
                                   format_phone_number)

from stoqlib.reporting.template import (BaseStoqReport, SearchResultsReport,
                                        ObjectListReport)
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SaleOrderReport(BaseStoqReport):
    report_name = _("Sale Order")

    def __init__(self, filename, sale_order, *args, **kwargs):
        self.sale = sale_order
        BaseStoqReport.__init__(self, filename, SaleOrderReport.report_name,
                                do_footer=True, landscape=True, *args,
                                **kwargs)
        self._identify_client()
        self.add_blank_space()
        self._setup_items_table()

    def _identify_client(self):
        if not self.sale.client:
            self.add_paragraph(_(u'No Client'), style='Normal-Bold')
            return

        person = self.sale.client.person
        client = person.name

        phone_number = format_phone_number(person.phone_number)
        mobile_number = format_phone_number(person.mobile_number)
        addr = person.get_main_address()
        address = [addr.get_address_string(), addr.get_details_string()]
        document = self._get_person_document(person)

        cols = [TC('', style='Normal-Bold', width=80),
                TC('', expand=True, truncate=True),
                TC('', style='Normal-Bold', width=130), TC('', expand=True)]

        data = [[_(u'Client:'), client, _(u'Phone number:'), phone_number],
                [_(u'CPF/CNPJ:'), document, _(u'Mobile number'),
                 mobile_number],
                [_(u'Address:'), address[0], _(u'City/State:'), address[1]]]

        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER,
                              table_line=TABLE_LINE_BLANK)

    def _get_person_document(self, person):
        individual = IIndividual(person, None)
        if individual is not None:
            return individual.cpf
        company = ICompany(person, None)
        if company is not None:
            return company.cnpj

    def _get_table_columns(self):
        # XXX Bug #2430 will improve this part
        return [OTC(_("Code"), lambda obj: obj.sellable.code,
                    truncate=True, width=100),
                OTC(_("Item"),
                    lambda obj: obj.sellable.description,
                    truncate=True, expand=True),
                OTC(_("Quantity"), lambda obj: obj.get_quantity_unit_string(),
                    width=80, align=RIGHT),
                OTC(_("Price"), lambda obj: get_formatted_price(obj.price),
                    width=90, align=RIGHT),
                OTC(_("Sub-Total"),
                    lambda obj: get_formatted_price(obj.get_total()),
                    width=100, align=RIGHT)]

    def _setup_items_table(self):
        # XXX Bug #2430 will improve this part
        items_qty = self.sale.get_items_total_quantity()
        total_value = get_formatted_price(self.sale.get_sale_subtotal())
        if items_qty > 1:
            items_text = _("%s items") % format_quantity(items_qty)
        else:
            items_text = _("%s item") % format_quantity(items_qty)
        summary = ["", "", items_text, "", total_value]
        self.add_object_table(list(self.sale.get_items()),
                              self._get_table_columns(), summary_row=summary)
        # sale details
        cols = [TC('', expand=True), TC('', width=100, align='RIGHT'),
                TC('', width=100, style='Normal-Bold', align='RIGHT')]

        discount = get_formatted_price(self.sale.discount_value)
        total = get_formatted_price(self.sale.get_total_sale_amount())
        data = [['', _(u'Discount:'), discount], ['', _(u'Total:'), total]]

        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER,
                              table_line=TABLE_LINE_BLANK)
        self._add_sale_notes()

    def _add_sale_notes(self):
        details_str = self.sale.get_details_str()

        if details_str:
            self.add_paragraph(_(u'Additional Information'), style='Normal-Bold')
            self.add_preformatted_text(details_str, style='Normal-Notes')

    def _get_status_date(self, status):
        status_date = {Sale.STATUS_INITIAL: 'open_date',
                       Sale.STATUS_ORDERED: 'open_date',
                       Sale.STATUS_CONFIRMED: 'confirm_date',
                       Sale.STATUS_PAID: 'close_date',
                       Sale.STATUS_CANCELLED: 'cancel_date',
                       Sale.STATUS_QUOTE: 'open_date',
                       Sale.STATUS_RETURNED: 'return_date',
                       Sale.STATUS_RENEGOTIATED: 'close_date'}
        return getattr(self.sale, status_date[status])

    #
    # BaseReportTemplate hooks
    #

    def get_title(self):
        return _(u'Number: %s - Sale %s on %s') % (
                    self.sale.get_order_number_str(),
                    Sale.get_status_name(self.sale.status),
                    self._get_status_date(self.sale.status).strftime('%x'))


class SalesReport(ObjectListReport):
    # This should be properly verified on BaseStoqReport. Waiting for
    # bug 2517
    obj_type = SaleView
    report_name = _("Sales Report")
    main_object_name = (_("sale"), _("sales"))
    filter_format_string = _("with status <u>%s</u>")

    def __init__(self, filename, objectlist, sale_list, *args, **kwargs):
        self.sale_list = sale_list
        ObjectListReport.__init__(self, filename, objectlist, sale_list,
                                  SalesReport.report_name,
                                  landscape=True,
                                  *args, **kwargs)
        self._setup_sales_table()

    def _setup_sales_table(self):
        total = sum([sale.total or currency(0) for sale in self.sale_list])
        self.add_summary_by_column(_(u'Total'), get_formatted_price(total))
        self.add_object_table(self.sale_list, self.get_columns(),
                              summary_row=self.get_summary_row())


class SoldItemsByBranchReport(ObjectListReport):
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
    # This should be properly verified on BaseStoqReport. Waiting for
    # bug 2517
    obj_type = CommissionView
    report_name = _("Sales")

    def __init__(self, filename, salesperson_list, salesperson_name,
                 *args, **kwargs):
        branch = get_current_branch(get_connection()).get_description()
        self.salesperson_list = salesperson_list

        if salesperson_name:
            singular = _("sale from {salesperson} on branch {branch}").format(
                         salesperson=salesperson_name, branch=branch)
            plural = _("sales from {salesperson} on branch {branch}").format(
                       salesperson=salesperson_name, branch=branch)
        else:
            singular = _("sale on branch %s") % branch
            plural = _("sales on branch %s") % branch

        self.main_object_name = (singular, plural)

        SearchResultsReport.__init__(self, filename, salesperson_list,
                                     SalesPersonReport.report_name,
                                     landscape=(salesperson_name is None),
                                     *args, **kwargs)
        self._sales_person = salesperson_name
        self._setup_sales_person_table()

    def _get_columns(self):
        columns = []
        if self._sales_person is None:
            columns.append(OTC(_("Name"), lambda obj: obj.salesperson_name,
                           expand=True, truncate=True, width=245))
        columns.extend([
            OTC(_("Total Amount"), lambda obj: get_formatted_price(
                obj.get_total_amount()), truncate=True, width=105),
            OTC(_("P/A"), lambda obj: get_formatted_price(
                obj.get_payment_amount()), truncate=True, width=90),
            OTC(_("Percentage"), lambda obj: get_formatted_percentage(
                obj.commission_percentage), truncate=True,
                width=100),
            OTC(_("Value"), lambda obj: get_formatted_price(
                obj.commission_value), truncate=True, width=80),
            OTC(_("S/P"), lambda obj: format_quantity(obj.quantity_sold()),
                width=45, truncate=True)])
        return columns

    def _setup_sales_person_table(self):
        total_amount = total_payment = total_percentage = total_value = \
            total_sold = 0
        for commission_view in self.salesperson_list:
            total_amount += commission_view.get_total_amount()
            total_payment += commission_view.get_payment_amount()
            total_value += commission_view.commission_value
            total_sold += commission_view.quantity_sold()

        if total_amount > 0:
            total_percentage = total_value * 100 / total_amount
        else:
            total_percentage = 0

        summary_row = ["", _("Total:"), get_formatted_price(total_amount),
                       get_formatted_price(total_payment),
                       get_formatted_percentage(total_percentage),
                       get_formatted_price(total_value),
                       format_quantity(total_sold)]

        # salesperson_list might have multiples items that refers to the
        # same sale. This will count the right number of sales.
        sales_qty = len([s.id for s in self.salesperson_list
                                    if not s.sale_returned()])

        text = None
        if self._sales_person is not None:
            summary_row.pop(0)
            va = 0
            if total_amount:
                va = total_amount / sales_qty
            text = _("Sold value per sales %s") % (get_formatted_price(va, ))

        self.add_object_table(self.salesperson_list, self._get_columns(),
                              summary_row=summary_row)

        self.add_preformatted_text(_("P/A: Payment Amount"))
        self.add_preformatted_text(_("S/P: Sellables sold per sale"))
        if text:
            self.add_preformatted_text(text)
            self.add_preformatted_text(_("Total of sales: %d") % sales_qty)
