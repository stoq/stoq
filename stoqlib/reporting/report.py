# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2012 Async Open Source
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import weasyprint

from kiwi.accessor import kgetattr
from kiwi.environ import environ

from stoqlib.database.runtime import get_default_store
from stoqlib.lib.template import render_template
from stoqlib.lib.translation import stoqlib_gettext, stoqlib_ngettext
from stoqlib.lib.formatters import (get_formatted_price, get_formatted_cost,
                                    format_quantity, format_phone_number,
                                    get_formatted_percentage)
from stoqlib.reporting.utils import get_logo_data
_ = stoqlib_gettext


class HTMLReport(object):
    template_filename = None
    title = ''
    complete_header = True

    def __init__(self, filename):
        self.filename = filename
        self.logo_data = get_logo_data(get_default_store())

    def _get_formatters(self):
        return {
            'format_price': get_formatted_price,
            'format_cost': get_formatted_cost,
            'format_quantity': format_quantity,
            'format_percentage': get_formatted_percentage,
            'format_phone': format_phone_number,
            'format_date': lambda d: d and d.strftime('%x') or '',
        }

    def get_html(self):
        assert self.title
        namespace = self.get_namespace()
        # Set some defaults if the report did not provide one
        namespace.setdefault('subtitle', '')
        namespace.setdefault('notes', [])

        # Add some filters commonly used in stoq
        namespace.update(self._get_formatters())

        return render_template(self.template_filename,
                               report=self,
                               title=self.title,
                               complete_header=self.complete_header,
                               _=stoqlib_gettext,
                               stoqlib_ngettext=stoqlib_ngettext,
                               **namespace)

    def save_html(self, filename):
        html = open(filename, 'w')
        html.write(self.get_html())
        html.flush()

    def render(self, stylesheet=None):
        template_dir = environ.get_resource_filename('stoq', 'template')
        html = weasyprint.HTML(string=self.get_html(),
                               base_url=template_dir)

        return html.render(stylesheets=[weasyprint.CSS(string=stylesheet)])

    def save(self):
        document = self.render(stylesheet='')
        document.write_pdf(self.filename)

    #
    # Hook methods
    #

    def get_namespace(self):
        """This hook method can be implemented by children and should return
        parameters that will be passed to report template in form of a dict.
        """
        return {}

    def adjust_for_test(self):
        """This hook method must be implemented by children that generates
        reports with data that change with the workstation or point in time.
        This allows for the test reports to be always generated with the same
        data.
        """
        self.logo_data = 'logo.png'


class TableReport(HTMLReport):
    """A report that contains a single table.

    Subclasses must implement get_columns and get_row, and can optionaly
    implement accumulate, reset and get_summary_row.
    """

    #: The title of the report. Will be present in the header.
    title = None

    #:
    subtitle_template = _("Listing {rows} of a total of {total_rows} {item}")

    #:
    main_object_name = (_("item"), _("items"))

    #:
    filter_format_string = ""

    #:
    complete_header = False

    #:
    template_filename = "objectlist.html"

    def __init__(self, filename, data, title=None, blocked_records=0,
                 status_name=None, filter_strings=None, status=None):
        self.title = title or self.title
        self.blocked_records = blocked_records
        self.status_name = status_name
        self.status = status
        if filter_strings is None:
            filter_strings = []
        self.filter_strings = filter_strings
        self.data = data
        self.columns = self.get_columns()

        self._setup_details()
        HTMLReport.__init__(self, filename)

    def _setup_details(self):
        """ This method build the report title based on the arguments sent
        by SearchBar to its class constructor.
        """
        rows = len(self.data)
        total_rows = rows + self.blocked_records
        item = stoqlib_ngettext(self.main_object_name[0],
                                self.main_object_name[1], total_rows)
        self.subtitle = self.subtitle_template.format(rows=rows,
                                                      total_rows=total_rows, item=item)

        base_note = ""
        if self.filter_format_string and self.status_name:
            base_note += self.filter_format_string % self.status_name.lower()

        notes = []
        for filter_string in self.filter_strings:
            if base_note:
                notes.append('%s %s' % (base_note, filter_string))
            elif filter_string:
                notes.append(filter_string)
        self.notes = notes

    def get_data(self):
        self.reset()
        for obj in self.data:
            self.accumulate(obj)
            yield self.get_row(obj)

    def accumulate(self, row):
        """This method is called once for each row in the report.

        Here you can create summaries (like the sum of all payments) for the
        report, that will be added in the last row of the table
        """
        pass

    def reset(self):
        """This is called when the iteration on all the rows starts.

        Use this to setup or reset any necesary data (like the summaries)
        """
        pass

    def get_summary_row(self):
        """If the table needs a summary row in the end, this method should
        return the list of values that will be in this last row.

        The values should already be formatted for presentation.
        """
        return []

    def get_columns(self):
        """Get the columns for this table report.

        This should return a list of dictionaries defining each column in the
        table. The dictionaries should define the keys 'title', with the string
        that will be in the header of the table and 'align', for adjusting the
        alignment of the column ('left', 'right' or 'center')
        """
        raise NotImplementedError

    def get_row(self, obj):
        """Returns the data to be displayed in the row.

        Subclaases must implement this method and return a list of value for
        each cell in the row. This values should already be formatted correctly
        (ie, a date should already be converted to a string in the desired
        format).
        """
        raise NotImplementedError


class ObjectListReport(TableReport):
    """Creates an pdf report from an objectlist and its current state

    This report will only show the columns that are visible, in the order they
    are visible. It will also show the filters that were enabled when the report
    was generated.
    """

    #: Defines the columns that should have a summary in the last row of the
    #: report. This is a list of strings defining the attribute of the
    #: respective column. Currently, only numeric values are supported (Decimal,
    #: currenty, etc..).
    summary = []

    def __init__(self, filename, objectlist, data, *args, **kwargs):
        self._objectlist = objectlist
        TableReport.__init__(self, filename, data, *args, **kwargs)

    def get_columns(self):
        import gtk
        alignments = {
            gtk.JUSTIFY_LEFT: 'left',
            gtk.JUSTIFY_RIGHT: 'right',
            gtk.JUSTIFY_CENTER: 'center',
        }

        # The real columns from the objectlist
        self._columns = []
        columns = []
        for c in self._objectlist.get_columns():
            if not c.treeview_column.get_visible():
                continue
            if c.data_type == gtk.gdk.Pixbuf:
                continue

            self._columns.append(c)
            columns.append(dict(title=c.title, align=alignments.get(c.justify)))

        return columns

    def get_cell(self, obj, column):
        #XXX Maybe the default value should be ''
        return column.as_string(kgetattr(obj, column.attribute, None), obj)

    def get_row(self, obj):
        row = []
        for c in self._columns:
            row.append(self.get_cell(obj, c))
        return row

    def accumulate(self, row):
        """This method is called once for each row in the report.

        Here you can create summaries (like the sum of all payments) for the
        report, that will be added in the last row of the table
        """
        for i in self.summary:
            self._summary[i] += getattr(row, i, 0) or 0

    def reset(self):
        """This is called when the iteration on all the rows starts.

        Use this to setup or reset any necesary data (like the summaries)
        """
        self._summary = {}
        for i in self.summary:
            self._summary[i] = 0

    def get_summary_row(self):
        if not self.summary:
            return []

        row = []
        for column in self._columns:
            value = self._summary.get(column.attribute, '')
            if value:
                value = column.as_string(value)
            row.append(value)
        return row


class ObjectTreeReport(ObjectListReport):
    """Creates an pdf report from an objecttree and its current state

    This report will only show the columns that are visible, in the order they
    are visible. It will also show the filters that were enabled when the report
    was generated. And finnally display parent row in bold and children row
    shifted a little bit to the right
    """

    template_filename = "objecttree.html"

    def get_row(self, obj):
        row = []
        for c in self._columns:
            row.append(self.get_cell(obj, c))
        return self.has_parent(obj), row

    def has_parent(self, obj):
        raise NotImplementedError
