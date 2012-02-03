# -*- coding: utf-8 -*-
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Stoqlib Reporting tables implementation.  """

import gtk
from reportlab.platypus import TableStyle, LongTable as RTable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib import colors
from kiwi.log import Logger

from stoqlib.reporting.base.flowables import (LEFT, CENTER, RIGHT,
                                              Paragraph)
from stoqlib.reporting.base.default_style import (TABLE_HEADER_FONT,
                                                  TABLE_HEADER_FONT_SIZE,
                                                  TABLE_HEADER_TEXT_COLOR,
                                                  TABLE_HEADER_BACKGROUND,
                                                  HIGHLIGHT_COLOR,
                                                  TABLE_LINE,
                                                  COL_PADDING,
                                                  SOFT_LINE_COLOR)

log = Logger("stoqlib.reporting")

# Highlight rules:
HIGHLIGHT_ODD = 1
HIGHLIGHT_EVEN = 2
HIGHLIGHT_ALWAYS = 3
HIGHLIGHT_NEVER = 4


class Table(RTable):
    """ Extension of Reportlab Table """
    def __init__(self, data, colWidths=None, rowHeights=None, style=None,
                 repeatRows=0, repeatCols=0, splitByRow=True,
                 emptyTableAction=None, ident=None, hAlign=None, vAlign=None,
                 width=None, align=CENTER, **kwargs):
        """ This class extend Reportlab table supplying extra checks on its
        methods, what is an extra utility to the developer.
        """
        hAlign = hAlign or align
        self._width = width
        RTable.__init__(self, data, colWidths, rowHeights, style, repeatRows,
                        repeatCols, splitByRow, emptyTableAction,
                        **kwargs)
        if vAlign:
            self.vAlign = vAlign
        self.hAlign = hAlign

    def wrap(self, avail_width, avail_height):
        """ Calculate the space required by the table. Internal use by
        Reportlab.
        """
        total_width = sum([w or 0 for w in self._colWidths if w != "*"])
        # Resize columns if needed
        if total_width > avail_width:
            log.warning("The column width (%f) is greater than the available "
                        "space (%r), diff = %f" % (total_width, avail_width,
                                                   total_width - avail_width))

            for i, width in enumerate(self._colWidths):
                if width in (None, '*'):
                    continue

                self._colWidths[i] = (float(width) / total_width) * avail_width

            self._argW = self._colWidths

        return RTable.wrap(self, self._width or avail_width, avail_height)

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
        """ Creates a new AbstractTableBuilder object

        @param data:   The table rows.
        @type:         list

        @param style:  The table style.
        @type:         TableStyle
        """
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
        self.extra_rows.append([Paragraph(str(d), style="TableCell")
                                    for d in row_data])

    #
    # Hooks
    #

    def get_data(self):
        """ Returns all the table lines plus the extra row, if any. """
        return self.data + self.extra_rows

    def update_style(self):
        """ Implement this method on subclass to define your own table styles.
        """


class DataTableBuilder(AbstractTableBuilder):
    """ Data table builder """

    #
    # AbstractTableBuilder Hooks
    #

    def get_data(self):
        result = []
        for row in self.data:
            result.append([])
            for cell_idx, cell in enumerate(row):
                if not cell_idx % 2:
                    data = Paragraph(cell, style="TableHeader", align=TA_RIGHT)
                else:
                    data = Paragraph(cell, style="TableCell")
                result[-1].append(data)
        return result

    def update_style(self):
        """ Apply the data table style. """
        columns = max(map(len, self.data))
        for col_idx in range(2, columns - 1, 2):
            self.style.add('LEFTPADDING',
                           (col_idx, 0),
                           (col_idx, - 1),
                           10)
            self.style.add('RIGHTPADDING',
                           (col_idx - 1, 0),
                           (col_idx - 1, -1),
                           10)
            self.style.add('LINEBEFORE',
                           (col_idx, 0),
                           (col_idx, -1),
                           0.5,
                           SOFT_LINE_COLOR)


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
        return AbstractTableBuilder.create_table(self, *args, **kwargs)

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
            style.add('LINEBELOW', (0, 0), (-1, 0), *self.table_line)
            style.add('FONTNAME', (0, 0), (-1, 0), TABLE_HEADER_FONT)
            style.add('FONTSIZE', (0, 0), (-1, 0), TABLE_HEADER_FONT_SIZE)
            style.add('TEXTCOLOR', (0, 0), (-1, 0), TABLE_HEADER_TEXT_COLOR)
            style.add('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BACKGROUND)
        else:
            border_reach -= 1
        if self.highlight != HIGHLIGHT_NEVER:
            for i in range(0, len(self.data), 2):
                if self.header:
                    i += 1
                style.add('BACKGROUND', (0, i), (-1, i), HIGHLIGHT_COLOR)
        style.add('BOX', (0, 0), (-1, border_reach), *self.table_line)


class ColumnTableBuilder(ReportTableBuilder):
    """ Column table builder """
    # Note that extra_row needs to be formatted according to the column
    # specification provided.
    def __init__(self, data, columns, style=None, progress_handler=None,
                 table_line=TABLE_LINE, do_header=True, extra_row=None,
                 summary_row=None, width=None):
        """ Creates a new ColumnTableBuilder object

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

        @param summary_row: A list of strings to be inserted after the table
                       and that means the sum of one or more columns.
        @type:         list
        """
        self.columns = columns
        self.progress_handler = progress_handler
        if do_header:
            header = self._get_header()
        else:
            header = None
        # Both paramenters are not allowed.
        if summary_row and extra_row is None:
            extra_row = summary_row
        self.has_summary_row = summary_row is not None
        ReportTableBuilder.__init__(self, self.build_data(data), style,
                                    header, table_line, extra_row)

    def create_table(self, *args, **kwargs):
        """ Override ReportTableBuilder create_table method to allow specify
        the columns width.
        """
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
            headers.append(Paragraph(col.name, style="TableHeader",
                                     align=col.get_translated_alignment()))
        return headers

    #
    # AbstractTableBuilder hooks
    #

    # XXX: AbstractTableBuilder's add_row() overwrite to able of to
    # align properly the extra row's columns.
    def add_row(self, data):
        extra_row = [Paragraph(str(data), style="TableCell",
                               align=col.get_translated_alignment(),
                               ellipsize=col.truncate)
                           for data, col in zip(data, self.columns)]
        self.extra_rows.append(extra_row)

    def update_style(self):
        """ Apply the column table style. """
        ReportTableBuilder.update_style(self)
        for idx, col in enumerate(self.columns):
            col.update_style(self.style, idx,
                             has_summary_row=self.has_summary_row,
                             table_line=self.table_line)


class ObjectTableBuilder(ColumnTableBuilder):
    """ Object table builder """
    def __init__(self, objs, columns, style=None, width=None,
                 progress_handler=None, table_line=TABLE_LINE,
                 extra_row=None, summary_row=None):
        """ Creates a new ObjectTableBuilder object

        @param objs: A instance list, where each instance is a table row.
        @type  objs: list.
        @param columns: A list of ObjectTableColumn, representing the
          table columns.
        @type  columns: list
        @param style: The table style.
        @type  style: TableStyle
        @param width: The table width.
        @type  width: int
        @param table_line: Define the type of the line that is inserted between
          the table rows.
        @type table_line: One of TABLE_LINE or TABLE_LINE_BLANK constants.
        @param extra_row: An object with data to be inserted right after
          the table. This data is included on the report as a normal data
          table after this object table.
        @type extra_row: list
        @param summary_row: A list of strings to be inserted after the table
          and that means the sum of one or more columns.
        @type summary_row: list
        """
        if extra_row and summary_row:
            raise ValueError("You can't use extra_row and summary_row at "
                             "the same time!")
        self._expand_cols(columns, width)
        ColumnTableBuilder.__init__(self, objs, columns, style=style,
                                    progress_handler=progress_handler,
                                    table_line=table_line, extra_row=extra_row,
                                    summary_row=summary_row)

    def _get_header(self):
        """ Return the column names representing the table header. """
        col_names = [col.name for col in self.columns]
        if not '' in col_names:
            headers = []
            for col in self.columns:
                p = Paragraph(col.name, style="TableHeader",
                              align=col.get_translated_alignment())
                col.max_width = max(col.max_width, p.get_width())
                headers.append(p)
            return headers

        # If we set a virtual column in a table without header, the first line
        # (the supposed header) will have spanned cells
        if 1 in [c.virtual for c in self.columns]:
            raise RuntimeError('Virtual columns in a table (%r) without'
                               ' headers is not implemented' % self)
        return None

    def create_table(self, *args, **kwargs):
        """ Override ReportTableBuilder create_table method to allow specify
        the columns width.
        """
        def choose_width(column):
            return min(col.width, col.max_width)

        col_widths = [choose_width(col) for col in self.columns]
        return ReportTableBuilder.create_table(self, colWidths=col_widths)

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

        total_expand = sum([col.expand_factor for col in cols])

        if total_expand and None in col_widths:
            msg = 'You cannot use auto-sized (%r) and expandable ' \
                  ' columns on the same table (%r)'
            raise ValueError(msg % (cols[col_widths.index(None)], self))

        if width and not total_expand:
            raise ValueError('Setting table width without expanded'
                             ' col(s) doesn\'t make sense.')

        if total_expand and not width:
            raise ValueError('Expandable cols can only be used with '
                              'fixed width table.')

        total_width = sum([w or 0 for w in col_widths])

        if width and total_width > width:
            msg = 'Columns width sum (%.2f) can\'t exceed table width (%.2f).'
            raise RuntimeError(msg % (total_width, width))

        if total_expand:
            extra_width = width - total_width - COL_PADDING * len(cols)
            for col in cols:
                expand_width = extra_width * col.expand_factor / total_expand
                col.width += expand_width


class NewObjectTableBuilder(AbstractTableBuilder):
    """ A new implementation of ObjectTableBuilder, which accepts Kiwi's
    ObjectList columns. """

    alignment_translate_dict = {gtk.JUSTIFY_CENTER: TA_CENTER,
                                gtk.JUSTIFY_LEFT: TA_LEFT,
                                gtk.JUSTIFY_RIGHT: TA_RIGHT}

    def __init__(self, objs, cols, width=None, highlight=HIGHLIGHT_ALWAYS):
        self._columns, self._col_widths = \
                       zip(*[(col, col.width or "*")
                                 for col in cols if col.visible])
        self._header = self._get_header()
        self._highlight = highlight
        self._width = width
        AbstractTableBuilder.__init__(self, objs)

    def _translate_alignment(self, col):
        if not col.justify in NewObjectTableBuilder.alignment_translate_dict:
            raise TypeError("Invalid alignment for column %r, got %r" %
                            (col, col.justify))
        return NewObjectTableBuilder.alignment_translate_dict[col.justify]

    def _get_header(self):
        titles = [col.title for col in self._columns]
        if None not in titles:
            return [Paragraph(title, style="TableHeader",
                              align=self._translate_alignment(col))
                      for title, col in zip(titles, self._columns)]
        return None

    def update_style(self):
        self.style.add("GRID", (0, 0), (-1, -1), 1, colors.black)
        if self._highlight != HIGHLIGHT_NEVER:
            if self._header:
                start_idx = 1
            else:
                start_idx = 0
            for i in range(start_idx, len(self.data), 2):
                self.style.add("BACKGROUND", (0, i), (-1, i), HIGHLIGHT_COLOR)

    def create_table(self, width=None):
        if self._header:
            repeat_rows = 1
        else:
            repeat_rows = 0
        return AbstractTableBuilder.create_table(self, width=width,
                                                 colWidths=self._col_widths,
                                                 repeatRows=repeat_rows)

    def get_data(self):
        style = "TableCell"
        data = [[Paragraph(col.as_string(col.get_attribute(row, col.attribute)),
                           style=style, align=self._translate_alignment(col))
                     for col in self._columns]
                for row in self.data]
        if self._header:
            data.insert(0, self._header)
        return data


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

        style.add('LINEBEFORE', (0, 0), (0, -1), *TABLE_LINE)
        style.add('LINEABOVE', (0, 0), (-1, 0), *TABLE_LINE)
        style.add('LINEBELOW', (0, 0), (-1, -1), *TABLE_LINE)

    def update_header_style(self):
        style = self.style
        header = self.header
        style.add('LINEBELOW', (0, 0), (-1, 0), *TABLE_LINE)
        style.add('FONTNAME', (0, 0), (-1, 0), TABLE_HEADER_FONT)
        style.add('FONTSIZE', (0, 0), (-1, 0), TABLE_HEADER_FONT_SIZE)
        style.add('TEXTCOLOR', (0, 0), (-1, 0), TABLE_HEADER_TEXT_COLOR)
        style.add('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BACKGROUND)
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
                widths = self.column_widths[col_idx:col_idx + col.colspan]
                col.width = sum(widths)
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
            colspan = col.colspan
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
                 format_func=None, truncate=False, expand=False, align=LEFT,
                 virtual=False, style='TableCell'):
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

        @param expand: Must this column expand?
        @type:         bool

        @param virtual: If True, then the column *omit* its separator with the
                       last column and its header will be expanded with the one
                       of last column.
        @type:         bool
        @param style:  The cell style, defaults to 'TableCell'.
        @type:         str
        """
        self.name = name
        self.width = width
        # Keep score of this columns's cells max with, so we dont waste space
        self.max_width = 0
        self.format_string = format_string
        self.format_func = format_func
        self.truncate = truncate
        self._align = align
        self.expand = expand
        self.virtual = virtual
        self._style = style

    def get_translated_alignment(self):
        if self._align == LEFT:
            return TA_LEFT
        elif self._align == RIGHT:
            return TA_RIGHT
        elif self._align == CENTER:
            return TA_CENTER
        else:
            raise ValueError("Invalid alignment specifed for column %r: %r"
                             % (self, self._align))

    def get_string_data(self, value):
        """  Returns the column value. The value can be returned through
        accessors defined by the user. """
        if self.format_func:
            value = self.format_func(value)
        if self.format_string:
            value = self.format_string % value
        if not isinstance(value, basestring):
            value = str(value)
        p = Paragraph(value, style=self._style, ellipsize=self.truncate,
                      align=self.get_translated_alignment())
        self.max_width = max(self.max_width, p.get_width())
        return p

    def __repr__(self):
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))

    def update_style(self, style, idx, has_summary_row=False,
                     table_line=TABLE_LINE):
        """ Apply the column style. """
        if self.virtual:
            style.add('SPAN', (idx - 1, 0), (idx, 0))
        else:
            j = has_summary_row and 1 or 0
            style.add('LINEBEFORE', (idx, 0), (idx, -1 - j),
                      *table_line)


class ObjectTableColumn(TableColumn):
    def __init__(self, name, data_source, expand_factor=0, align=LEFT,
                 truncate=False, width=None, format_string=None,
                 format_func=None, expand=False, virtual=False,
                 style=None, *args, **kwargs):
        """ Creates a new ObjectTableColumn object

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

        @param truncate: If True, the column value will be truncate if its size
                       was greater than the column width.
        @type:         bool
        """
        self.data_source = data_source
        self.expand_factor = expand_factor
        # FIXME: Fix it, args/kwargs are horrible here
        self._callable_kwargs = kwargs
        self._callable_args = args
        TableColumn.__init__(self, name, width=width, truncate=truncate,
                             format_string=format_string, expand=expand,
                             format_func=format_func, virtual=virtual,
                             align=align)

    def get_string_data(self, value):
        """  Returns the column value. The value can be returned through
        accessors defined by the user. """
        if self.data_source is None:
            return ''
        if isinstance(self.data_source, str):
            # XXX Dangerous function = eval.
            data = eval(self.data_source)
            if callable(data):
                data = data(*self._callable_args, **self._callable_kwargs)
        elif callable(self.data_source):
            data = self.data_source(value)
        return TableColumn.get_string_data(self, data)

    def __repr__(self):
        return '<ObjectTableColumn name: %s at 0x%x>' % (self.name, id(self))


class GroupingTableColumn(ObjectTableColumn):
    """ This column type works like ObjectTableColumn but it doesn't implements
    the expand attribute, nor virtual columns. This class must be used with
    objects that needs more than one line to represents its data.
    """
    def __init__(self, data_source, colspan=1, format_string=None, align=LEFT,
                 truncate=False, width=None, virtual=False, format_func=None,
                 style=None):
        self.colspan = colspan
        # We don't have a name atribute for this class. So, we just use as None
        ObjectTableColumn.__init__(self, None, data_source, truncate=truncate,
                                   align=align, width=width,
                                   format_string=format_string,
                                   format_func=format_func, virtual=virtual,
                                   style=style)
