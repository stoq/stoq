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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Base class implementation for all Stoq reports """

from decimal import Decimal

import gtk
import pango

from kiwi.accessor import kgetattr
from kiwi.environ import environ
from kiwi.ui.objectlist import ObjectList
from mako.lookup import TemplateLookup
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from trml2pdf.trml2pdf import parseString

from stoqlib.database.runtime import (get_current_branch, get_connection,
                                      get_current_user)
from stoqlib.domain.interfaces import ICompany
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext, stoqlib_ngettext
from stoqlib.lib.formatters import format_phone_number, format_quantity
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
        timestamp = kwargs.get('do_footer', True)
        ReportTemplate.__init__(self, timestamp=timestamp,
                                username=self.get_username(), *args, **kwargs)
        logotype_path = _get_logotype_path(get_connection())
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
        person = get_current_branch(get_connection()).person
        main_address = person.get_main_address()
        company = ICompany(person, None)

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

        # Address lines
        address_string1 = ''

        address_parts = []
        if main_address:
            address_string1 = main_address.get_address_string()

            if main_address.postal_code:
                address_parts.append(main_address.postal_code)
            if main_address.get_city():
                address_parts.append(main_address.get_city())
            if main_address.get_state():
                address_parts.append(main_address.get_state())

        address_string2 = " - ".join(address_parts)

        # Contact line
        contact_parts = []
        if person.phone_number:
            contact_parts.append(_("Phone: %s")
                                   % format_phone_number(person.phone_number))
        if person.fax_number:
            contact_parts.append(_("Fax: %s")
                                   % format_phone_number(person.fax_number))

        contact_string = ' - '.join(contact_parts)

        # Company details line
        company_parts = []
        if company:
            if company.get_cnpj_number():
                company_parts.append(_("CNPJ: %s") % company.cnpj)
            if company.get_state_registry_number():
                company_parts.append(_("State Registry: %s")
                                       % company.state_registry)

        company_details_string = ' - '.join(company_parts)

        for text in (address_string1, address_string2, contact_string,
                     company_details_string):
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

    def get_username(self):
        user = get_current_user(get_connection())
        return user.person.name[:45]


class SearchResultsReport(BaseStoqReport):
    """ This class is very useful for reports based on SearchBar results.
    Based on the main object name used on the report, this class build
    the BaseStoqReport title's notes with the search criteria defined by
    the user on the GUI.
    """
    # Translators: e.g: Product Listing - Listing 34 of a total of 45 products
    summary = _("{title} - Listing {rows} of a total of {total_rows} {item}")

    main_object_name = (_("item"), _("items"))
    filter_format_string = ""

    def __init__(self, filename, data, report_name, blocked_records=0,
                 status_name=None, filter_strings=[], status=None,
                 *args, **kwargs):
        self._blocked_records = blocked_records
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
        rows = len(self._data)
        total_rows = rows + self._blocked_records
        item = stoqlib_ngettext(self.main_object_name[0],
                                self.main_object_name[1], total_rows)
        title = self.summary.format(title=self.report_name, rows=rows,
                                    total_rows=total_rows, item=item)

        base_note = ""
        if self.filter_format_string and self._status_name:
            base_note += self.filter_format_string % self._status_name.lower()

        notes = []
        for filter_string in self._filter_strings:
            if base_note:
                notes.append('%s %s' % (base_note, filter_string))
            elif filter_string:
                notes.append(filter_string)
        return (title, notes)


class ObjectListReport(SearchResultsReport):
    def __init__(self, filename, objectlist, data, report_name,
                 *args, **kwargs):
        self._columns = []
        if not isinstance(objectlist, ObjectList):
            raise TypeError("objectlist must be a ObjectList, not a %r" % (
                objectlist, ))
        self.objectlist = objectlist
        self._summary_row = {}
        SearchResultsReport.__init__(self, filename, data, report_name,
                                     *args, **kwargs)

    def _convert_column(self, column):
        # Converts objectlist.Column to ObjectTableColumn
        if column.ellipsize == pango.ELLIPSIZE_NONE:
            truncate = False
        else:
            truncate = True

        if column.justify == gtk.JUSTIFY_RIGHT:
            align = 'RIGHT'
        elif column.justify == gtk.JUSTIFY_CENTER:
            align = 'CENTER'
        else:
            align = 'LEFT'

        width = column.treeview_column.get_width()
        # Ignore width when expand parameter is set or the column will not be
        # expanded.
        if column.expand:
            width = None
        # Avoid the use of format_string and format_func by using the data
        # already formatted.
        data_source = lambda obj: column.as_string(
                                    kgetattr(obj, column.attribute, None))
        return OTC(name=column.title, data_source=data_source, align=align,
                   truncate=truncate, width=width, expand=column.expand)

    def _setup_columns_from_list(self):

        report_columns = []
        for column in self.objectlist.get_columns():
            if not column.treeview_column.get_visible():
                continue
            # Not supported columns.
            if column.data_type in [bool, gtk.gdk.Pixbuf]:
                continue

            report_columns.append(self._convert_column(column))
        return report_columns

    #
    # Public API
    #

    def get_columns(self):
        """Returns the report columns.

        @returns: a list of ObjectTableColumns.
        """
        if not self._columns:
            self._columns = self._setup_columns_from_list()
        return self._columns

    def add_summary_by_column(self, column_name, value):
        """Includes the summary of a certain column in the summary row.

        @param column_name: the name of the summarized column.
        @param value: the summary value.
        """
        self._summary_row.update({column_name: value})

    def get_summary_row(self):
        """Returns the row used to summarize data.

        @returns: the summary row.
        """
        row = []
        for column in self.get_columns():
            row.append(self._summary_row.get(column.name, ''))
        if any(row) and row[0] == '':
            row[0] = _(u'Totals:')

        return row


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
        return [OTC(_("Code"), lambda obj: obj.code, width=100, truncate=True),
                OTC(_("Description"), lambda obj: obj.description,
                    truncate=True),
                OTC(_("Price"), lambda obj: obj.price, width=60,
                    truncate=True),
            ]

    def _setup_items_table(self):
        total_price = 0
        for item in self._items:
            total_price += item.price or Decimal(0)
        summary_row = ["", _("Total:"), format_quantity(total_price)]
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
            (self.__class__.__name, ))
