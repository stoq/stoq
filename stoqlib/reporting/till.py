# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2007 Async Open Source <http://www.async.com.br>
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
""" Till report implementation """


from storm.expr import And

from stoqlib.domain.till import TillClosedView
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.reporting.report import ObjectListReport, HTMLReport

N_ = _


class TillHistoryReport(ObjectListReport):
    """This report show a list of the till history returned by a SearchBar,
    listing both its description, date and value.
    """
    title = _("Till History Listing")
    main_object_name = (_("till entry"), _("till entries"))
    summary = ['value']


class TillDailyMovementReport(HTMLReport):
    """This report shows all the financial transactions on till
    """
    template_filename = 'till/till.html'
    title = _('Daily Movement')
    complete_header = False

    def __init__(self, filename, store, branch, daterange, data_object):
        self.branch = branch
        self.start_date = daterange[0]
        self.end_date = daterange[1]
        self.sales = data_object.sales
        self.lonely_in_payments = data_object.lonely_in_payments
        self.purchases = data_object.purchases
        self.lonely_out_payments = data_object.lonely_out_payments
        self.return_sales = data_object.return_sales
        self.till_supplies = data_object.till_supplies
        self.till_removals = data_object.till_removals
        self.method_summary = data_object.method_summary
        self.card_summary = data_object.card_summary

        queries = [TillClosedView.opening_date >= self.start_date,
                   TillClosedView.opening_date <= self.end_date]
        if branch:
            queries.append(TillClosedView.branch_id == branch.id)
        self.tills = store.find(TillClosedView, And(queries))

        HTMLReport.__init__(self, filename)

    #
    #  HTMLReport
    #

    def get_subtitle(self):
        """Returns a subtitle text
        """
        if self.end_date:
            return _('Till movement on %s to %s') % (self.start_date,
                                                     self.end_date)
        return _('Till movement on %s') % self.start_date

    def get_namespace(self):
        if self.branch is None:
            return dict(notes=[_('All Branches')])
        return dict(notes=[self.branch.get_description()])

    def has_in_payments(self):
        return bool(self.sales or self.lonely_in_payments)

    def has_out_payments(self):
        return bool(self.purchases or self.lonely_out_payments or self.return_sales)

    def has_till_entries(self):
        return bool(self.till_supplies or self.till_removals)
