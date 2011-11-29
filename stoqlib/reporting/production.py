# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
""" Production report implementation """

from decimal import Decimal

from stoqlib.reporting.base.default_style import TABLE_LINE_BLANK
from stoqlib.reporting.base.flowables import LEFT, RIGHT
from stoqlib.reporting.base.tables import (TableColumn as TC,
                                           ObjectTableColumn as OTC,
                                           HIGHLIGHT_NEVER)
from stoqlib.reporting.template import BaseStoqReport, ObjectListReport
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.domain.views import ProductionItemView


class ProductionItemReport(ObjectListReport):
    """ This report show a list of all production items returned by a SearchBar,
    listing both its description, category and its quantities.
    """
    # This should be properly verified on SearchResultsReport. Waiting for
    # bug 2517
    obj_type = ProductionItemView
    report_name = _("Production Item Listing")
    filter_format_string = _("on branch <u>%s</u>")

    def __init__(self, filename, objectlist, production_items,
                 *args, **kwargs):
        self._production_items = production_items
        ObjectListReport.__init__(self, filename, objectlist, production_items,
                                  ProductionItemReport.report_name,
                                  landscape=True, *args, **kwargs)
        self._setup_items_table()

    def _setup_items_table(self):
        totals = [(p.quantity or Decimal(0),
                   p.produced or Decimal(0),
                   p.lost or Decimal(0)) for p in self._production_items]
        qty, produced, lost = zip(*totals)
        self.add_summary_by_column(_(u'To Produce'), format_quantity(sum(qty)))
        self.add_summary_by_column(_(u'Produced'),
                                   format_quantity(sum(produced)))
        self.add_summary_by_column(_(u'Lost'), format_quantity(sum(lost)))

        self.add_object_table(self._production_items, self.get_columns(),
                              summary_row=self.get_summary_row())


class ProductionReport(ObjectListReport):
    report_name = _(u'Production Order Report')
    main_object_name = (_("order"), _("orders"))
    filter_format_string = _(u'with status <u>%s</u>')

    def __init__(self, filename, objectlist, productions, status,
                 *args, **kwargs):
        ObjectListReport.__init__(self, filename, objectlist, productions,
                                  ProductionReport.report_name, landscape=True,
                                  *args, **kwargs)
        self.add_object_table(productions, self.get_columns())

    def get_title(self):
        return self.report_name


class ProductionOrderReport(BaseStoqReport):
    report_name = _(u'Production Order')

    def __init__(self, filename, production, *args, **kwargs):
        self._production = production
        BaseStoqReport.__init__(self, filename,
                                ProductionOrderReport.report_name,
                                landscape=True, *args, **kwargs)
        self._setup_production_details_table()
        self.add_blank_space(10)
        self._setup_production_items_table()
        self.add_blank_space(10)
        self._setup_material_items_table()
        self.add_blank_space(10)
        self._setup_service_items_table()

    def _setup_production_details_table(self):
        cols = [TC('', width=100), TC('', width=230, expand=True,
                                      truncate=True),
                TC('', width=150), TC('', width=230, expand=True,
                                      truncate=True),
        ]

        if self._production.expected_start_date:
            expected = self._production.expected_start_date.strftime('%x')
        else:
            expected = ''

        if self._production.close_date:
            close_date = self._production.close_date.strftime('%x')
        else:
            close_date = ''

        data = [[_(u'Open Date:'), self._production.open_date.strftime('%x'),
                _(u'Expected Start Date:'), expected],
                [_(u'Close Date:'), close_date,
                 _(u'Status'), self._production.get_status_string()],
                [_(u'Reponsible:'), self._production.get_responsible_name(),
                _(u'Branch:'), self._production.get_branch_name()],
        ]
        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER, margins=2,
                              table_line=TABLE_LINE_BLANK, width=730)

    def _setup_production_items_table(self):
        self.add_paragraph(_(u'Production Items'), style='Title')
        items = list(self._production.get_items())
        total_quantity = Decimal(0)
        total_produced = Decimal(0)
        total_lost = Decimal(0)
        for item in items:
            total_quantity += item.quantity
            total_produced += item.produced
            total_lost += item.lost
        extra_row = ['', _(u'Totals:'), format_quantity(total_quantity),
                     format_quantity(total_produced),
                     format_quantity(total_lost)]
        self.add_object_table(items, self._get_production_items_columns(),
                              extra_row=extra_row)

    def _get_production_items_columns(self):
        return [
            OTC(_(u'Description'), lambda obj: '%s' % obj.get_description(),
                expand=True, truncate=True),
            OTC(_(u'Unit'), lambda obj: '%s' % obj.get_unit_description(),
                align=LEFT, width=60),
            OTC(_(u'Quantity'), lambda obj: '%s' % format_quantity(
                obj.quantity), align=RIGHT, width=100),
            OTC(_(u'Produced'), lambda obj: '%s' % format_quantity(
               obj.produced), align=RIGHT, width=100),
            OTC(_(u'Lost'), lambda obj: '%s' % format_quantity(
               obj.lost), align=RIGHT, width=100)]

    def _setup_material_items_table(self):
        self.add_paragraph(_(u'Materials'), style='Title')
        materials = list(self._production.get_material_items())
        total_needed = Decimal(0)
        total_lost = Decimal(0)
        total_purchase = Decimal(0)
        total_make = Decimal(0)
        for material in materials:
            total_needed += material.needed
            total_lost += material.lost
            total_purchase += material.to_purchase
            total_make += material.to_make
        extra_row = ['', '', _(u'Totals:'), format_quantity(total_needed),
                     format_quantity(total_lost),
                     format_quantity(total_purchase),
                     format_quantity(total_make)]
        self.add_object_table(materials, self._get_material_items_columns(),
                              extra_row=extra_row)

    def _get_material_items_columns(self):
        return [
            OTC(_(u'Description'), lambda obj: '%s' % obj.get_description(),
                expand=True, truncate=True),
            OTC(_(u'Location'), lambda obj: '%s' % obj.product.location,
                width=80),
            OTC(_(u'Unit'), lambda obj: '%s' % obj.get_unit_description(),
                align=LEFT, width=60),
            OTC(_(u'Needed'), lambda obj: '%s' % format_quantity(
                obj.needed), align=RIGHT, width=80),
            OTC(_(u'Lost'), lambda obj: '%s' % format_quantity(
               obj.lost), align=RIGHT, width=80),
            OTC(_(u'To Purchase'), lambda obj: '%s' % format_quantity(
               obj.to_purchase), align=RIGHT, width=80),
            OTC(_(u'To Make'), lambda obj: '%s' % format_quantity(
               obj.to_make), align=RIGHT, width=80)]

    def _setup_service_items_table(self):
        services = list(self._production.get_service_items())
        if not services:
            return
        total_quantity = sum([s.quantity for s in services], Decimal(0))
        extra_row = ['', _(u'Totals:'), total_quantity]
        self.add_paragraph(_(u'Services'), style='Title')
        self.add_object_table(services, self._get_service_items_columns(),
                              extra_row=extra_row)

    def _get_service_items_columns(self):
        return [
            OTC(_(u'Description'), lambda obj: '%s' % obj.get_description(),
                expand=True, truncate=True),
            OTC(_(u'Unit'), lambda obj: '%s' % obj.get_unit_description(),
                align=LEFT, width=60),
            OTC(_(u'Quantity'), lambda obj: '%s' % format_quantity(
                obj.quantity), align=RIGHT, width=100)]

    #
    # BaseStoqReport
    #

    def get_title(self):
        order_number = self._production.get_order_number()
        description = self._production.get_description()
        return '%s #%s - %s' % (self.report_name, order_number, description)
