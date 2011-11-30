# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
"""Implements the ReportTemplate class, an BaseReportTemplate extension
that allows footer and header drawing.
"""
import datetime

from reportlab.lib.units import mm

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.base.template import BaseReportTemplate
from stoqlib.reporting.base.default_style import (HIGHLIGHT_COLOR, SPACING,
                                                  TEXT_COLOR)

_ = stoqlib_gettext
SMALL_FONT = ("Vera", 12)


class ReportTemplate(BaseReportTemplate):
    """ An extension of BaseReportTemplate with methods to draw the report
    footer and header, just it.  Use this if you like headers and footer,
    otherwise look at BaseReportTemplate.
    """
    footer_height = 7 * mm
    report_name_prefix = ""

    def __init__(self, filename, report_name, timestamp=False, do_header=True,
                 do_footer=True, date=None, username=None, **kwargs):
        """ Common parameters to BaseReportTemplate was ommited, maybe
        you want look at BaseReportTemplate documentation?
        @param timestamp: The time when the report was created must be
                          drawed at the report footer? Defaults to False.
        @type timestamp:  bool
        @param do_header: Must a header be drawed on top of the report?
                          Defaults to True.
        @type do_header:  bool
        @param do_footer: Must a footer be drawed on each report page?
                          Defaults to True.
        @type do_footer:  bool

        """
        if timestamp and not do_footer:
            raise ValueError("You don't can have a timestamped footer if "
                             "you don't have a footer")
        self.timestamp = timestamp
        self.date = date
        self.username = username
        BaseReportTemplate.__init__(self, filename, report_name,
                                    do_header=do_header, do_footer=do_footer,
                                    **kwargs)

    def draw_header(self, canvas):
        """ Draws the report header (the thing where you can want to put your
        company logo).
        """
        # Sorry, not implemented yet
        return

    def get_report_name(self):
        return self.report_name_prefix + self.report_name

    def draw_footer(self, canvas):
        """Implementation of BaseReportTemplate hook. This method is called on
        footer drawing time if this object has the time_stamp attribute set to
        True (see this class constructor documentation.).
        The footer format is::

            [USERNAME]  DATE [TIME] Page X

        Where DATE is the date when the report was created, of course. TIME
        and USERNAME are optional, and X is the page number.
        """
        if self.date is None:
            ts = datetime.datetime.now()
        else:
            ts = self.date
        date_string = ts.strftime("%x")
        if self.timestamp:
            date_string += ts.strftime(" %X")
        page_number = _("Page % 2d") % self.get_page_number()

        # Let's start drawing
        canvas.setFillColor(HIGHLIGHT_COLOR)
        canvas.rect(self.leftMargin, self.bottomMargin, self.width,
                    self.footer_height, stroke=0, fill=1)
        text_y = self.bottomMargin + 0.5 * SPACING
        canvas.setFillColor(TEXT_COLOR)
        canvas.setFont(*SMALL_FONT)
        canvas.drawString(self.leftMargin + 0.5 * SPACING, text_y,
                          self.get_report_name())

        if self.username:
            date_string = '%s  %s' % (self.username, date_string)

        canvas.drawRightString(self._rightMargin - 75, text_y, date_string)
        canvas.drawRightString(self._rightMargin - 0.5 * SPACING, text_y,
                               page_number)
