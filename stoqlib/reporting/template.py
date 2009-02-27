# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
##  Author(s):  Henrique Romano         <henrique@async.com.br>
##              George Kussumoto        <george@async.com.br>
##
##
""" Base class implementation for all Stoq reports """

from decimal import Decimal

from kiwi.environ import environ
from mako.lookup import TemplateLookup
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from trml2pdf.trml2pdf import parseString

from stoqlib.database.runtime import (new_transaction,
                                get_current_branch, get_connection)
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import format_phone_number, format_quantity
from stoqlib.reporting.base.printing import ReportTemplate
from stoqlib.reporting.base.tables import ObjectTableColumn as OTC

_ = stoqlib_gettext


FANCYNAME_FONT = ("Vera-B", 14)
LOGO_SIZE = (171, 59)
SMALL_FONT = ("Vera", 12)
TEXT_HEIGHT = 13

def _get_logotype_path(trans):
   logofile = sysparam(trans).CUSTOM_LOGO_FOR_REPORTS
   if logofile.is_valid():
       logofile.resize(LOGO_SIZE)
       return str(logofile.image_path)
   else:
       return environ.find_resource("pixmaps", "stoq_logo_bgwhite.png")


class BaseStoqReport(ReportTemplate):
    logo_border = 5 * mm
    report_name_prefix = "Stoq - "

    def __init__(self, *args, **kwargs):
        ReportTemplate.__init__(self, *args, **kwargs)
        self.trans = new_transaction()
        logotype_path = _get_logotype_path(self.trans)
        self._logotype = ImageReader(logotype_path)
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

    def draw_header(self, canvas):
        canvas.saveState()
        person = get_current_branch(self.trans).person

        logo_width, logo_height = self._logotype.getSize()
        header_y = self._topMargin - logo_height - BaseStoqReport.logo_border
        header_x = self.leftMargin + BaseStoqReport.logo_border
        canvas.drawImage(self._logotype, header_x, header_y, logo_width,
                         logo_height)

        canvas.setFont(*FANCYNAME_FONT)
        text_x = header_x + logo_width + BaseStoqReport.logo_border
        text_y = header_y + logo_height - BaseStoqReport.logo_border
        if not person.name:
            raise DatabaseInconsistency("The person by ID %d should have a "
                                        "name at this point" % person.id)
        canvas.drawString(text_x, text_y, person.name)

        canvas.setFont(*SMALL_FONT)

        main_address = person.get_main_address()
        if main_address:
            address_string1 = main_address.get_address_string()
            address_string2 = []
            if main_address.postal_code:
                address_string2.append(main_address.postal_code)
            if main_address.get_city() and main_address.get_state():
                address_string2.extend([main_address.get_city(),
                                        main_address.get_state()])
            address_string2 = " - ".join(address_string2)
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
                 status_name=None, filter_strings=[], status=None, *args, **kwargs):
        self._blocked_records = None
        self._status_name = status_name
        self._status = status
        self._filter_strings = filter_strings
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
        main_object_name = (self.main_object_name or "")
        if self._blocked_records > 0:
            rows_qty = len(self._data)
            title += (_("%d of a total of %d %s")
                      % (rows_qty, rows_qty + self._blocked_records,
                         main_object_name))
        else:
            if main_object_name:
                title += _("all %s") % main_object_name
        base_note = ""
        if self.filter_format_string and self._status_name:
            base_note += self.filter_format_string % self._status_name.lower()

        notes = []
        for filter_string in self._filter_strings:
            if base_note:
                notes.append('%s %s' % (base_note, filter_string,))
            elif filter_string:
                notes.append(filter_string)
        return (title, notes)


class PriceReport(SearchResultsReport):
    """ This is a base report which shows a list of items returned by a
    SearchBar listing both it's description and price.
    """
    # This should be properly verified on SearchResultsReport. Waiting for
    # bug 2517
    report_name = ""

    def __init__(self, filename, items, *args, **kwargs):
        self._items = items
        SearchResultsReport.__init__(self, filename, items, self.report_name,
                                     landscape=False, *args, **kwargs)
        self._setup_items_table()

    def _get_columns(self):
        return [OTC(_("Code"), lambda obj: '%03d' % obj.id, width=60,
                    truncate=True),
                OTC(_("Description"), lambda obj: obj.description,
                    truncate=True),
                OTC(_("Price"), lambda obj: obj.price, width=60,
                    truncate=True),
            ]

    def _setup_items_table(self):
        total_price = 0
        for item in self._items:
            total_price += item.price or Decimal(0)
        summary_row = ["",  _("Total:"), format_quantity(total_price)]
        self.add_object_table(self._items, self._get_columns(),
                              summary_row=summary_row)


class BaseRMLReport(object):
    """
    A base class for all rml reports
    @cvar template_name: the name of the template to be used in report
    @cvar title: the report title
    """
    template_name = None
    title = _('Untitled')

    def __init__(self, filename, template_name=None):
        """ Creates a new BaseRMLReport object

        @param filename: filename to save report as
        @param template_name: optional, name of the rml template to use
        """
        template_name = template_name or self.template_name
        lookup = TemplateLookup(directories=environ.get_resource_paths('template'))
        self._template = lookup.get_template(template_name)
        self.filename = filename

    def save(self):
        """Build the report file properly"""
        ns = self.get_namespace()
        if not type(ns) is dict:
            raise TypeError(
                "%s.get_namespace must return a dictionary, not $r" %
                (self.__class__.__name__, ns))
        self._complete_namespace(ns)
        template = self._template.render(**ns)
        pdf_file = open(self.filename, 'w')
        # create the pdf file
        pdf_file.write(parseString(template))
        pdf_file.close()

    def _complete_namespace(self, ns):
        """Add common information in namespace
        """
        conn = get_connection()
        branch = get_current_branch(conn)
        branch_address = branch.person.address
        logo = _get_logotype_path(conn)

        ns['title'] = self.title
        ns['logo'] = logo
        ns['branch'] = branch

    def get_namespace(self):
        """
        Each child must to build your namespace and implement this
        method to give us a common way to access it
        """
        raise NotImplementedError(
            '%s needs to implement get_namespace()' %
            (self.__class__.__name,))
