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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
##  Author(s):  Henrique Romano         <henrique@async.com.br>
##
##
""" Base class implementation for all Stoq reports """

from kiwi.environ import environ
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

from stoqlib.reporting.base.printing import ReportTemplate
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.runtime import new_transaction
from stoqlib.lib.validators import format_phone_number
from stoqlib.domain.interfaces import ICompany
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


# FIXME: We must consider using TTF fonts here (UTF-8 issues)
FANCYNAME_FONT = ("Vera-B", 14)
SMALL_FONT = ("Vera", 12)
TEXT_HEIGHT = 13


class BaseStoqReport(ReportTemplate):
    logo_border = 5 * mm
    report_name_prefix = "Stoq - "

    def __init__(self, *args, **kwargs):
        ReportTemplate.__init__(self, *args, **kwargs)
        self.conn = new_transaction()
        self._logotype = self._get_logotype()
        # The BaseReportTemplate's header_height attribute define the
        # vertical position where the document really must starts be
        # drawed (this is used to not override the space reserved to
        # the logotype)
        self.header_height = (self._logotype.getSize()[1]
                              + BaseStoqReport.logo_border)
        title = self.get_title()
        if title:
            if not type(title) is tuple:
                title = (title, )
            self.add_title(*title)

    def _get_logotype(self):
        logofile = environ.find_resource("pixmaps", "stoq_logo_bgwhite.png")
        return ImageReader(logofile)

    def draw_header(self, canvas):
        canvas.saveState()
        person = sysparam(self.conn).CURRENT_BRANCH.get_adapted()
        company = ICompany(person)

        logo_width, logo_height = self._logotype.getSize()
        header_y = self._topMargin - logo_height - BaseStoqReport.logo_border
        header_x = self.leftMargin + BaseStoqReport.logo_border
        canvas.drawImage(self._logotype, header_x, header_y, logo_width,
                         logo_height)

        canvas.setFont(*FANCYNAME_FONT)
        text_x = header_x + logo_width + BaseStoqReport.logo_border
        text_y = header_y + logo_height - BaseStoqReport.logo_border
        canvas.drawString(text_x, text_y, company.fancy_name)

        canvas.setFont(*SMALL_FONT)

        main_address = person.get_main_address()
        if main_address:
            address_string1 = main_address.get_address_string()
            address_string2 = ""
            if main_address.postal_code:
                address_string2 += "%s - " % main_address.postal_code
            address_string2 += "%s - %s" % (main_address.get_city(),
                                            main_address.get_state())
        else:
            address_string1 = address_string2 = ''

        if person.phone_number:
            contact_string = (_("Phone: %s")
                              % format_phone_number(person.phone_number))
        else:
            contact_string = ''
        if person.fax_number:
            fax_str = _("Fax: %s") % format_phone_number(person.fax_number)
            contact_string += " - %s" % fax_str

        for text in (address_string1, address_string2, contact_string):
            text_y -= TEXT_HEIGHT
            canvas.drawString(text_x, text_y, text)
        canvas.restoreState()

    #
    # Hooks
    #

    def _initialize(self):
        pass

    def get_title(self):
        raise NotImplementedError


class SearchResultsReport(BaseStoqReport):
    """ This class is very useful for reports based on SearchBar results.
    Based on the main object name used on the report, this class build
    the BaseStoqReport title's notes with the search criteria defined by
    the user on the GUI.
    """
    main_object_name = None
    filter_format_string = ""

    def __init__(self, filename, data, report_name, blocked_records=None,
                 status_name=None, extra_filters=None, start_date=None,
                 end_date=None, status=None, *args, **kwargs):
        self._blocked_records = None
        self._status_name = status_name
        self._status = status
        self._extra_filters = extra_filters
        self._start_date = start_date
        self._end_date = end_date
        self._data = data
        BaseStoqReport.__init__(self, filename, report_name, *args, **kwargs)

    #
    # BaseStoqReport hooks
    #

    def get_title(self):
        """ This method build the report title based on the arguments sent
        by SearchBar to its class constructor.
        """
        title = self.report_name.capitalize()
        title += " - %s " % _("Listing")
        main_object_name = (self.main_object_name
                            and self.main_object_name.lower() or "")
        if self._blocked_records > 0:
            rows_qty = len(self._data)
            title += (_("%d of a total of %d %s")
                      % (rows_qty, rows_qty + self._blocked_records,
                         main_object_name))
        else:
            if main_object_name:
                title += _("all %s") % main_object_name
        notes = ""
        if self.filter_format_string and self._status_name:
            notes += self.filter_format_string % self._status_name.lower()
        if self._extra_filters:
            notes += " %s " % (_("matching \"%s\"")
                               % self._extra_filters)
        if self._start_date:
            if self._end_date:
                notes += (_("between %s and %s")
                          % (self._start_date.strftime("%x"),
                             self._end_date.strftime("%x")))
            else:
                notes += (_("and since %s")
                          % self._start_date.strftime("%x"))
        elif self._end_date:
            notes += (_("until %s")
                      % self._end_date.strftime("%x"))
        if notes:
            notes = "%s %s" % (self.main_object_name.capitalize(), notes)
        return (title, notes)
