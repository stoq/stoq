# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Henrique Romano             <henrique@async.com.br>
##
""" Stoqlib Reporting tables implementation.  """

import operator

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import TableStyle, Paragraph, Table as RTable

from stoqlib.reporting.flowables import LEFT, CENTER, RIGHT
from stoqlib.reporting.default_style import (TABLE_HEADER_FONT,
                                             TABLE_HEADER_FONT_SIZE,
                                             TABLE_HEADER_TEXT_COLOR,
                                             TABLE_HEADER_BACKGROUND,
                                             HIGHLIGHT_COLOR,
                                             TABLE_LINE,
                                             COL_PADDING,
                                             SOFT_LINE_COLOR,
                                             DEFAULT_FONTNAME,
                                             DEFAULT_FONTSIZE)

# Highlight rules:
HIGHLIGHT_ODD = 1
HIGHLIGHT_EVEN = 2
HIGHLIGHT_ALWAYS = 3
HIGHLIGHT_NEVER = 4

class Table(RTable):
    """ Extension of Reportlab Table """
    def __init__(self, data, *args, **kwargs):
        """ This class extend Reportlab table supplying extra checks on its
        methods, what is an extra utility to the developer.
        """
        # Reportlab's Table class doesn't provide a better API to set
        # alignment, so we need to handle this specially. We need to be
        # specially careful here because Tables are instantiated by
        # reportlab behind our backs (when splitting tables into pages):
        # we are required to keep the exact same interface as table.
        # This has impact on *Template's create_table, where they stuff
        # align into kwargs -- it used to be a third argument to Table's
        # constructor, and it didn't work!
        if kwargs.has_key("align"):
            align = kwargs["align"]
            del kwargs["align"]
        else:
            align = CENTER
        RTable.__init__(self, data, *args, **kwargs)
        self.hAlign = align

    def wrap(self, avail_width, avail_height):
        """ Calculate the space required by the table. Internal use by
        Reportlab.
        """
        # If Reportlab doesn't try to calculate the table width before drawning
        # it out of the sheet, we do it for Reportlab.
        total_width = reduce(operator.add, [w or 0 for w in self._colWidths])
        if  total_width > avail_width:
            # We don't use %r on the error message because reportlab dumps all
            # table data instead of the representation. %s the same.
            msg = 'Width of table with columns %s exceeded canvas available ' \
                  'width in %.2f points.'
            raise RuntimeError, msg % (self._colWidths, total_width - avail_width)
        return RTable.wrap(self, avail_width, avail_height)

    def identity(self):
        return self.__repr__()

    def __repr__(self):
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

#
# Table builders
#

class AbstractTableBuilder:
    """ Abstract class for table creation """
    def __init__(self, data, style=None, extra_row=None):
        self.style = TableStyle(parent=style)
        self.data = data
        self.extra_rows = []
        if extra_row:
            self.add_row(extra_row)

    def create_table(self, *args, **kwargs):
        """ The table creation core """
        self.update_style()
        return Table(self.get_data(), style=self.style, *args, **kwargs)

    def add_row(self, row_data):
        """ Just add an extra row to the table """
        self.extra_rows.append(row_data)

    #
    # Hooks
    #

    def get_data(self):
        """ Returns all the table lines plus the extra row, if any.
        """
        return self.data + self.extra_rows

    def update_style(self):
        """ Implement this method on subclass to define your own table styles.
        """

class DataTableBuilder(AbstractTableBuilder):
    """ Data table builder """

    def __init__(self, data, style=None):
        """
        @param data:   The table rows.
        @type:         list

        @param style:  The table style.
        @type:         TableStyle
        """
        AbstractTableBuilder.__init__(self, data, style)

    #
    # AbstractTableBuilder Hooks
    #

    def update_style(self):
        """ Apply the data table style. """
        style = self.style
        columns = max(map(len, self.data))
        for i in range(columns):
            # Formatting header columns. Last column can not be a header
            if not i % 2 and i < columns - 1:
                style.add('FONTNAME', (i,0), (i,-1), TABLE_HEADER_FONT)
                style.add('FONTSIZE', (i,0), (i,-1), TABLE_HEADER_FONT_SIZE)
                style.add('ALIGN', (i,0), (i,-1), RIGHT)
                # First column don't need the separator
                if i:
                    style.add('LINEBEFORE', (i,0), (i,-1), 0.5, SOFT_LINE_COLOR)
                    style.add('LEFTPADDING', (i,0), (i,-1), 10)
                    style.add('RIGHTPADDING', (i-1,0), (i-1,-1), 10)

    def get_data(self):
        """ Returns all the table rows. """
        return self.data

class ReportTableBuilder(AbstractTableBuilder):
    """ Report table builder """
    highlight = HIGHLIGHT_ODD
    def __init__(self, data, style=None, header=None, table_line=TABLE_LINE,
                 extra_row=None):
        self.header = header
        self.table_line = table_line
        AbstractTableBuilder.__init__(self, data, style=style,
                                      extra_row=extra_row)

    def set_highlight(self, highlight):
        """ Set the table highlight type:

        @param highlight: The highlight type
        @type:         One of HIGHLIGHT_ODD, HIGHLIGHT_NEVER, HIGHLIGHT_ALWAYS
                       constants
        """
        self.highlight = highlight

    def create_table(self, *args, **kwargs):
        """ Override the AbstractTableBuilder create_table method to allow
        pass extra parameters to Table class.
        """
        if self.header:
            kwargs['repeatRows'] = 1
        self.update_style()
        data = self.get_data()
        return Table(data, style=self.style, *args, **kwargs)

    #
    # AbstractTableBuilder Hooks
    #

    def get_data(self):
        """ Return all the table rows """
        if self.header:
            self.data.insert(0, self.header)
        return AbstractTableBuilder.get_data(self)

    def update_style(self):
        """ Apply the report table style. """
        style = self.style
        border_reach = len(self.data)
        if self.header:
            style.add('LINEBELOW', (0,0), (-1,0), *self.table_line)
            style.add('FONTNAME', (0,0), (-1,0), TABLE_HEADER_FONT)
            style.add('FONTSIZE', (0,0), (-1,0), TABLE_HEADER_FONT_SIZE)
            style.add('TEXTCOLOR', (0,0), (-1,0), TABLE_HEADER_TEXT_COLOR)
            style.add('BACKGROUND', (0,0), (-1,0), TABLE_HEADER_BACKGROUND)
        else:
            border_reach -= 1
        if self.highlight != HIGHLIGHT_NEVER:
            for i in range(0, len(self.data), 2):
                if self.header:
                    i += 1
                style.add('BACKGROUND', (0,i), (-1,i), HIGHLIGHT_COLOR)
        style.add('BOX', (0,0), (-1, border_reach), *self.table_line)

class ColumnTableBuilder(ReportTableBuilder):
    """ Column table builder """
    # Note that extra_row needs to be formatted according to the column
    # specification provided.
    def __init__(self, data, columns, style=None, progress_handler=None,
                 table_line=TABLE_LINE, do_header=1, extra_row=None):
        """
        @param data:   A list of lists, where each nested list represents a
                       row (naturally, each column of this nested list is a
                       table column).
        @type:         list

        @param columns: A list of TableColumn instances representing the
                       table columns
        @type:         list

        @param style:  The table style.
        @type          TableStyle

        @param table_line: Define the type of the line that is inserted between
                       the table rows.
        @type:         One of TABLE_LINE or TABLE_LINE_BLANK constants.

        @param do_header: Must the table header be drawed? Defaults to True
        @type:         bool

        @param extra_row: An list of strings to be inserted right after the
                       table.
        @type:         list
        """
        self.columns = columns
        self.progress_handler = progress_handler
        if do_header:
            header = self._get_header()
        else:
            header = None
        if extra_row:
            extra_row = self.get_row_data(extra_row)
        ReportTableBuilder.__init__(self, self.build_data(data), style,
                                    header, table_line, extra_row)

    def create_table(self, *args, **kwargs):
        """ Override ReportTableBuilder create_table method to allow specify
        the columns width. """
        col_widths = [col.width for col in self.columns]
        return ReportTableBuilder.create_table(self, colWidths=col_widths)

    def get_row_data(self, values):
        """ Returns all the row columns formatted """
        # In TableColumns, values is actually a list or tuple; we iterate
        # through that tuple and return the corresponding string_data
        return [column.get_string_data(value)
                    for (column, value) in zip(self.columns, values)]

    def build_data(self, data):
        """ Create the table rows list.

        @param data:   the row list passed by the user when creating the table
        @type:         list
        """
        prepared = []
        row_idx = 0
        list_len = len(data)
        step = int(list_len / 50) or 1
        for value in data:
            row_idx += 1
            data = self.get_row_data(value)
            prepared.append(data)
            if self.progress_handler is not None and not row_idx % step:
                self.progress_handler(row_idx, list_len)
        return prepared

    def _get_header(self):
        """ Returns a list with the column names. """
        headers = []
        for col in self.columns:
            if col.name is None:
                raise ValueError("Column name can not be None for "
                                 "ColumnTableBuilder instance")
            headers.append(col.name)
        return headers

    #
    # AbstractTableBuilder hooks
    #

    def update_style(self):
        """ Apply the column table style. """
        ReportTableBuilder.update_style(self)
        for idx, col in enumerate(self.columns):
            col.update_style(self.style, idx)

class ObjectTableBuilder(ColumnTableBuilder):
    """ Object table builder """
    def __init__(self, objs, columns, style=None, width=None,
                 progress_handler=None, table_line=TABLE_LINE,
                 extra_row=None):
        """
        @param objs:   A instance list, where each instance is a table row.
        @type:         list.

        @param columns:A list of ObjectTableColumn, representing the table
                       columns.
        @type:         list

        @param style:  The table style.
        @type:         TableStyle

        @param width:  The table width.
        @type:         int

        @param table_line: Define the type of the line that is inserted between
                       the table rows.
        @type:         One of TABLE_LINE or TABLE_LINE_BLANK constants.

        @param extra_row: An list of strings to be inserted right after
                       the table. This data is included on the report as
                       a normal data table after this object table.
        @type:         list
        """
        self._expand_cols(columns, width)
        ColumnTableBuilder.__init__(self, objs, columns, style=style,
                                    progress_handler=progress_handler,
                                    table_line=table_line, extra_row=extra_row)

    def _get_header(self):
        """ Return the column names representing the table header. """
        header = [col.name for col in self.columns]
        # Avoid passing a list of all empty headers
        if reduce(lambda h1, h2: h1 or h2, header):
            return header

        # If we set a virtual column in a table without header, the first line
        # (the supposed header) will have spanned cells
        if 1 in [c.virtual for c in self.columns]:
            raise RuntimeError, 'Virtual columns in a table (%r) without' \
                                ' headers is not implemented' % self
        return None

    def get_row_data(self, value):
        """ Create the row list, formatting its column values if needed. """
        ret = []
        for col in self.columns:
            ret.append(col.get_string_data(value))
        return ret

    def _expand_cols(self, cols, width):
        """ This method is used to apply column expansion based on its expand
        factors.
        """
        col_widths = [col.width for col in cols]

        total_expand = reduce(operator.add,
                              [col.expand_factor for col in cols])

        if total_expand and None in col_widths:
            msg = 'You cannot use auto-sized (%r) and expandable ' \
                  ' columns on the same table (%r)'
            raise ValueError, msg % (cols[col_widths.index(None)], self)

        if width and not total_expand:
            raise ValueError, 'Setting table width without expanded' \
                              ' col(s) doesn\'t make sense.'

        if total_expand and not width:
            raise ValueError, 'Expandable cols can only be used with ' \
                              'fixed width table.'

        total_width = reduce(operator.add, [w or 0 for w in col_widths])

        if width and total_width > width:
            msg = 'Columns width sum (%.2f) can\'t exceed table width (%.2f).'
            raise RuntimeError, msg % (total_width, width)

        if total_expand:
            extra_width = width - total_width - COL_PADDING * len(cols)
            for col in cols:
                expand_width = extra_width * col.expand_factor / total_expand
                col.width += expand_width

class GroupingTableBuilder(AbstractTableBuilder):
    def __init__(self, objs, column_groups, column_widths, style=None,
                 header=None, extra_row=None):
        self.objs = objs
        self.header = header
        self.column_groups = column_groups
        self.column_widths = column_widths

        self._setup_groups()
        self._setup_columns()

        AbstractTableBuilder.__init__(self, data=objs, style=style,
                                      extra_row=extra_row)

    def create_table(self, *args, **kwargs):
        kwargs['colWidths'] = self.column_widths
        if self.header:
            kwargs['repeatRows'] = 1
        return AbstractTableBuilder.create_table(self, *args, **kwargs)

    def get_data(self):
        data = []
        if self.header:
            data.append(self.header)
        obj_idx = 0
        for obj in self.objs:
            obj_data = []
            obj_idx += 1
            for col_group in self.column_groups:
                row_data = []
                for col in col_group.columns:
                    row_data.append(col.get_string_data(obj))
                    # We need to fill spanned cells with something to make
                    # reportlab happy.
                    row_data.extend([''] * (col.colspan - 1))
                obj_data.append(row_data)
            data.extend(obj_data)
        return data

    def update_style(self):
        style = self.style
        len_objs = len(self.objs)
        header = self.header

        if header:
            line_offset = 1
            self.update_header_style()
        else:
            line_offset = 0

        for group in self.column_groups:
            for obj_idx in range(len_objs):
                group.update_style(self.style, obj_idx, line_offset)

        style.add('LINEBEFORE', (0,0), (0,-1), *TABLE_LINE)
        style.add('LINEABOVE', (0,0), (-1,0), *TABLE_LINE)
        style.add('LINEBELOW', (0,0), (-1,-1), *TABLE_LINE)

    def update_header_style(self):
        style = self.style
        header = self.header
        style.add('LINEBELOW', (0,0), (-1,0), *TABLE_LINE)
        style.add('FONTNAME', (0,0), (-1,0), TABLE_HEADER_FONT)
        style.add('FONTSIZE', (0,0), (-1,0), TABLE_HEADER_FONT_SIZE)
        style.add('TEXTCOLOR', (0,0), (-1,0), TABLE_HEADER_TEXT_COLOR)
        style.add('BACKGROUND', (0,0), (-1,0), TABLE_HEADER_BACKGROUND)
        header_span = 0
        for i in range(len(header) - 1, -1, -1):
            if not header[i]:
                header_span += 1
                continue
            style.add('LINEAFTER', (i + header_span, 0),
                      (i + header_span, 0), *TABLE_LINE)
            if header_span:
                style.add('SPAN', (i, 0), (i + header_span, 0))
                header_span = 0

    def _setup_columns(self):
        for group in self.column_groups:
            col_idx = 0
            for col in group.columns:
                widths = self.column_widths[col_idx:col_idx+col.colspan]
                col.width = reduce(operator.add, widths)
                col_idx += col.colspan

    def _setup_groups(self):
        for group in self.column_groups:
            group.setup_group(self.column_groups)

class TableColumnGroup:
    """ This class groups GroupTableColumns columns """

    def __init__(self, columns, highlight=HIGHLIGHT_ODD):
        self.columns = columns
        self.highlight = highlight

    def setup_group(self, groups):
        self.total_columns = len(groups)
        self.group_idx = groups.index(self)

    def update_style(self, style, obj_idx, line_offset=0):
        """ Apply the column style """
        hl = self.highlight
        odd = not obj_idx % 2
        # line_idx is the calculated index of table lines
        line_idx = line_offset + self.group_idx + obj_idx * self.total_columns

        if hl == HIGHLIGHT_ALWAYS or (hl == HIGHLIGHT_ODD and odd) or \
                                     (hl == HIGHLIGHT_EVEN and not odd):

            style.add('BACKGROUND', (0, line_idx), (-1, line_idx),
                      HIGHLIGHT_COLOR)

        # span_offset is used to remember last spans
        span_offset = 0
        for idx, col in enumerate(self.columns):
            span = colspan - 1
            # x0. x1 are the begin / end of the spanned range
            x0 = idx + span_offset
            x1 = x0 + span
            if span:
                style.add('SPAN', (x0, line_idx), (x1, line_idx))
            # We add a vertical line after every spanned cells end.
            style.add('LINEAFTER', (x1, line_idx), (x1, line_idx),
                      *TABLE_LINE)
            span_offset += span
            col.update_style(style, x0)

    def __len__(self):
        return len(self.columns)

#
# Table Columns
#

class TableColumn:
    def __init__(self, name=None, width=None, format_string=None,
                 format_func=None, truncate=False, use_paragraph=False,
                 align=LEFT, *args, **kwargs):
        """ Column class for ColumnTable

        @param name:   The column name
        @type:         str

        @param width:  The column width
        @type:         float

        @param format_string: A string that will be used to format the column
                       value.
        @type:         str

        @param format_func: A function that will be called to format the column
                       value
        @type:

        @param truncate: Must be the string be truncate if its length was
                       greater than the colum width?
        @type:         bool


        @param use_paragraph: The the column content must be placed inside a
                       Reportlab paragraph.
        @type:         bool
        """
        self.name = name
        self.width = width
        self.format_string = format_string
        self.format_func = format_func
        self.truncate = truncate
        self.use_paragraph = use_paragraph
        self.align = align
        self.args = args
        self.kwargs = kwargs
        assert not (truncate and use_paragraph), \
            'What do you want for %s? Use paragraph or truncate?' % self

    def truncate_string(self, data):
        if not self.truncate or not len(data):
            return data
        if self.truncate and not self.width:
            msg = '%s can\'t truncate without a fixed width.' % self
            raise AssertionError, msg
        # XXX This piece of code is *ugly*, but works pretty well with
        # default font and padding.
        string_width = stringWidth(data, DEFAULT_FONTNAME,
                                   DEFAULT_FONTSIZE) or self.width
        # We remove four extra chars to keep the cell padding
        max = int(len(data) / (string_width / self.width)) - 4
        data = '\n'.join([l[:max] for l in data.split('\n')])
        return data

    def get_string_data(self, value):
        """  Returns the column value. The value can be returned through
        accessors defined by the user. """
        if self.format_func:
            value = self.format_func(value)
        if self.format_string:
            value = self.format_string % value
        value = self.truncate_string(value)
        if self.use_paragraph:
            value = Paragraph(value)
        return value

    def __repr__(self):
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

    def update_style(self, style, idx):
        """ Apply the column style. """
        if self.align:
            style.add('ALIGN', (idx,0), (idx,-1), self.align)
        else:
            style.add('LINEBEFORE', (idx,0), (idx,-1), *TABLE_LINE)

class ObjectTableColumn(TableColumn):
    """ ObjectTableColumn implementation """

    def __init__(self, name, data_source, expand_factor=0, align=LEFT,
                 virtual=0, truncate=0, *args, **kwargs):
        """
        @param name:   The column name
        @type:         str

        @param data_source: The attribute name where get the column value from.
                       This can be a callable object too.
        @type:         object

        @param expand_factor: The column expand factor.
        @type:         float

        @param align:  The table alignment. One of LEFT, RIGHT, CENTER
                       constants defined on stoqlib reporting flowables module.
        @type:         One of LEFT, RIGHT or CENTER

        @param virtual: If True, then the column *omit* its separator with the
                       last column and it header will be expanded with the one
                       of last column.
        @type:         bool

        @param truncate: If True, the column value will be truncate if its size
                       was greater than the column width.
        @type:         bool
        """
        self.data_source = data_source
        self.expand_factor = expand_factor
        self.virtual = virtual
        TableColumn.__init__(self, name, truncate=truncate, align=align,
                             *args, **kwargs)

    def get_string_data(self, value):
        """  Returns the column value. The value can be returned through
        accessors defined by the user. """
        if self.data_source is None:
            return ''
        if isinstance(self.data_source, str):
            locals().update(self.kwargs)
            # XXX Dangerous function = eval.
            data = eval(self.data_source)
            if callable(data):
                data = data(*self.args, **self.kwargs)
        elif callable(self.data_source):
            data = self.data_source(value, *self.args, **self.kwargs)
        return TableColumn.get_string_data(self, data)

    def update_style(self, style, idx):
        """ Apply the column style. """
        assert idx or not self.virtual, \
            'The first column can\'t be a virtual column'
        if self.align:
            style.add('ALIGN', (idx,0), (idx,-1), self.align)
        if self.virtual:
            style.add('SPAN', (idx-1, 0), (idx, 0))
        else:
            style.add('LINEBEFORE', (idx,0), (idx,-1), *TABLE_LINE)

    def __repr__(self):
        return '<ObjectTableColumn name: %s at 0x%x>' % (self.name, id(self))

class GroupingTableColumn(ObjectTableColumn):
    """ This column type works like ObjectTableColumn but it doesn't implements
    the expand attribute, nor virtual columns. This class must be used with
    objects that needs more than one line to represents its data.
    """
    def __init__(self, data_source, colspan=1, align=LEFT, truncate=0,
                 *args, **kwargs):
        self.colspan = colspan
        # We don't have a name atribute for this class. So, we just use None
        # for that.
        ObjectTableColumn.__init__(self, None, data_source, truncate=truncate,
                                   align=align, *args, **kwargs)

    def update_style(self, style, idx):
        """ Apply the column style. """
        if self.align:
            style.add('ALIGN', (idx,0), (idx,-1), self.align)

