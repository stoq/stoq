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
""" Here are implemented the BaseReportTemplate class, the class that represents
    the document itself,  with all the methods to elements insertion.
"""

from reportlab.lib import pagesizes
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                KeepTogether, PageBreak, Spacer)
from reportlab.platypus.flowables import Preformatted

from stoqlib.reporting.base import tables, flowables
from stoqlib.reporting.base.default_style import (DOC_DEFAULTS, SPACING,
                                                 STYLE_SHEET, TABLE_STYLE,
                                                 DEFAULT_MARGIN, TABLE_LINE)
from stoqlib.reporting.base.flowables import Paragraph


class BaseReportTemplate(BaseDocTemplate):
    """ Base class representing the document itself. Here is implemented all the
    methods to reporting elements insertion, like signatures, tables, paragraphs
    and so on.
    """
    header_height = 0
    footer_height = 0

    def __init__(self, filename, report_name, pagesize=pagesizes.A4,
                 landscape=0, do_header=0, do_footer=0, **kwargs):
        """ The parameters are:

        @param filename:    The filename where the report will saved to (since
                            the package only works with PDF files right now, it
                            is desirable a .pdf extension right after the name)
        @type filename:     str
        @param report_name: The name used to fill the report footer.
        @type report_name:  str
        @param pagesize:    The pagesize, no secrets here. Defaults to A4.
        @type pagesize:     One of the constants available on
                            reportlab.lib.pagesizes module.
        @param landscape:   Define if the report must be drawed in the landscape
                            format. Defaults to False.
        @type landscape:    bool
        @param do_footer:   Must the report footer be drawed? Defaults to False
        @type do_footer:    bool
        """
        self._do_header = do_header
        self._do_footer = do_footer
        self.report_name = report_name

        doc_kwargs = DOC_DEFAULTS.copy()
        doc_kwargs.update(kwargs)

        if landscape:
            pagesize = pagesizes.landscape(pagesize)

        BaseDocTemplate.__init__(self, filename, pagesize=pagesize,
                                 title=report_name, **doc_kwargs)
        self.flowables = []
        self.grouping = 0
        # Group of flowables wich shouldn't be separated on different pages
        self._together_flowables = []
        # Number of flowables to include in the current group.
        self._together_count = 0

    #
    # External API
    #

    def save(self):
        """ Build and saves the report. Internal use (you don't need to call
        this method in most of the cases).
        """
        self.build()

    def build(self):
        """ Build the report - initialize all the pages and start drawing its
        elements. Internal use (you don't need to call this method in most of
        the cases).
        """
        # Adds forgotten flowables
        self.end_group()

        # If page size has changed, we try to make ReportLab work
        self._calc()

        self.setup_page_templates()
        BaseDocTemplate.build(self, self.flowables)

    #
    # Doc structure
    #

    def setup_page_templates(self):
        """ Report initialization. Here we have to initialize report control
        attributes. """
        frame_y = self.bottomMargin
        height = self.height

        if self._do_header:
            height -= self.header_height

        if self._do_footer:
            height -= self.footer_height
            frame_y += self.footer_height

        main_frame = Frame(self.leftMargin, frame_y, self.width, height,
                           bottomPadding=SPACING, topPadding=SPACING)

        template = PageTemplate(id='Normal', frames=main_frame,
                                pagesize=self.pagesize,
                                onPage=self.paint_page_canvas)
        self.addPageTemplates([template])

    #
    # Internal API
    #

    def add(self, flowable):
        """ Adds a flowable to report. """
        if self.grouping:
            self._together_flowables.append(flowable)
            self.end_group(self._together_count - 1)
        else:
            self.flowables.append(flowable)

    def start_group(self):
        """ Starts flowables groupping. """
        self.grouping = 1

    def end_group(self, min_flowables=0):
        """ Finish flowables groupping """
        # Updating _together_count
        if min_flowables >= 0:
            self._together_count = min_flowables
        # If there is not more flowables, close the group and add it.
        if not min_flowables:
            self.grouping = 0
            if self._together_flowables:
                self.add(KeepTogether(self._together_flowables))
            self._together_flowables = []

    def get_usable_width(self):
        """ Returns the horizontal space available for drawing. """
        return self._rightMargin - self.leftMargin

    def get_usable_height(self):
        """ Returns the vertical space available for drawing. """
        return self._topMargin - self.bottomMargin

    def set_page_number(self, number):
        """ Sets the current page.

        @param number: The new page number.
        @type number:  int
        """
        self.add(flowables.PageNumberChanger(number))

    def get_page_number(self):
        """ Returns the current page number """
        return self.page

    #
    # Features
    #

    def add_page_break(self):
        """ Adds a simple page break """
        self.add(PageBreak())

    def add_document_break(self):
        """ This method adds a document break, starting a new document. """
        self.set_page_number(0)
        self.add_page_break()

    def add_blank_space(self, height=10, width=-1):
        """ Adds a blank space on the current report position. Through
        height e width parameters is possible defines the space type that
        we want, i.e, a vertical space (in this case, we pass width=-1
        and height=X, where represents the space desired) or a horizontal
        space (height=-1, width=X). The default is a vertical space.
        @param height: How much vertical space?
        @type height:  int/float
        @param width:  How much horizontal space?
        @type width:   int/float
        """
        self.add(Spacer(width, height))

    def add_signatures(self, labels, *args, **kwargs):
        """ Adds a signature flowable.

        @param labels:     A list of signatures (text). For list greater than 1
                           the signatures will be put side by side on the report.
        @type labels:      list
        @param align:      Set the signatures group alignment.
        @type align:       One of LEFT, CENTER or RIGHT constants defined in the
                           stoqlib reporting flowables module.
        @param line_width: The signature line width.
        @type line_width:  int/float
        @param height:     How much space before the signature?
        @type height:      int/float
        @param text_align: The signature text alignment.
        @type text_align:  One of LEFT, CENTER or RIGHT constants defined in the
                           stoqlib reporting flowables module.
        @param style_data: An optional paragraph style for the signature text.
        @type style_data:  One of paragraph styles defined in the default_style
                           method.
        """
        self.add(flowables.Signature(labels, *args, **kwargs))

    def add_preformatted_text(self, text, style='Raw', *args, **kwargs):
        """ Adds a given given text to the document, using a given
        style. ('Raw' by default)

        @param text:   The text.
        @type text:    str
        @param style:  One of the paragraph style names defined in the
                       default_style module. Defaults to 'Raw' style.
        @type style:   str
        """
        style = STYLE_SHEET[style]
        self.add(Preformatted(text, style, *args, **kwargs))

    def add_paragraph(self, text, style="Normal", **kwargs):
        """ Adds a paragraph to the document, using a given style.
        ('Normal by default')

        @param text:   The paragraph text.
        @type text:    str
        @param style:  One of the paragraph style names defined in the
                       default_style module
        @type style:   str
        """
        self.add(Paragraph(text, style, **kwargs))

    def add_line(self, *args, **kwargs):
        """ Insert a simple line on the report. """
        line = flowables.ReportLine(*args, **kwargs)
        self.add(line)

    def add_title(self, title, notes=[], space_before=SPACING,
                  style='Title', note_style='Title-Note'):
        """ Adds a title. The title flowable is composed of a text inside two
        separators.  Title notes also can be inserted, in this case an extra
        text will be put below the title.

        @param title:        The title text.
        @type title:         str
        @param note:         The title notes.
        @type note:          list
        @param space_before: How much space (in mm) must be given before the
                             title can be drawed? Defaults to the SPACING constant
                             defined on default_style module
        @type space_before:  float
        @param style:        One of the style names defined on the default_style
                             module.
        @type style:         str
        @param note_style:   One of the style names defined on the default_style
                             module
        @type note_style:    str
        """
        self.add_blank_space(space_before)
        self.start_group()
        self.add_line(v_margins=1)
        self.add_paragraph(title, style=style)
        for note in notes:
            self.add_paragraph(note, style=note_style)
        self.add_line(v_margins=1)
        self.end_group(1)
    #
    # Tables related methods
    #

    def add_report_table(self, data, header=None, style=TABLE_STYLE,
                         margins=DEFAULT_MARGIN, align=flowables.CENTER,
                         extra_row=None, table_line=TABLE_LINE,
                         highlight=tables.HIGHLIGHT_ODD, *args, **kwargs):
        """ Inserts a report table.

        @param data:       A list of lists, where each nested list represents a
                           row (naturally, each column of this nested list is a
                           table column).
        @type data:        list
        @param header:     A list of string representing the header of each
                           column.
        @type header:      list
        @param style:      The table style.
        @type style        TableStyle
        @param margins:    How much space before and after the table?
        @type margins      float/int
        @param align:      The table alignment. One of LEFT, RIGHT, CENTER
                           constants defined on stoqlib reporting flowables module.
        @type align:       One of LEFT, RIGHT or CENTER
        @param extra_row:  An list of strings to be inserted right after
                           the table.
        @type extra_row:   list
        @param table_line: Define the type of the line that is inserted between
                           the table rows.
        @type table_line:  One of TABLE_LINE or TABLE_LINE_BLANK constants.
        @param highlight:  Sets the table highlight type.
        @type highlight:   One of HIGHLIGHT_ODD, HIGHLIGHT_NEVER or HIGHLIGHT_ODD
                           constants defined on stoqlib reporting tables module.
        """
        self.add_blank_space(margins)
        table_builder = tables.ReportTableBuilder(data, style, header,
                                                  table_line,
                                                  extra_row=extra_row)
        kwargs["align"] = align
        table_builder.set_highlight(highlight)
        self.add(table_builder.create_table(*args, **kwargs))
        self.add_blank_space(margins)

    def add_column_table(self, data, columns, style=TABLE_STYLE,
                         margins=DEFAULT_MARGIN, align=flowables.CENTER,
                         extra_row=None, table_line=TABLE_LINE, do_header=True,
                         highlight=tables.HIGHLIGHT_ODD, *args, **kwargs):
        """ Adds a column table.

        @param data:       A list of lists, where each nested list represents a
                           row (naturally, each column of this nested list is a
                           table column).
        @type data:        list
        @param columns:    A list of TableColumn instances representing the
                           table columns
        @type columns:     list
        @param style:      The table style.
        @type style        TableStyle
        @param margins:    How much space before and after the table?
        @type margins:     float/int
        @param align:      The table alignment. One of LEFT, RIGHT, CENTER
                           constants defined on stoqlib reporting flowables module.
        @type align:       One of LEFT, RIGHT or CENTER
        @param extra_row:  An list of strings to be inserted right after
                           the table.
        @type extra_row:   list
        @param table_line: Define the type of the line that is inserted between
                           the table rows.
        @type table_line:  One of TABLE_LINE or TABLE_LINE_BLANK constants.
        @param do_header:  Must the table header be drawed? Defaults to True
        @type do_header:   bool
        @param highlight:  Sets the table highlight type.
        @type highlight:   One of HIGHLIGHT_ODD, HIGHLIGHT_NEVER or HIGHLIGHT_ODD
                           constants defined on stoqlib reporting tables module.
        """
        self.add_blank_space(margins)
        table_builder = tables.ColumnTableBuilder(data, columns, style=style,
                                                  table_line=table_line,
                                                  do_header=do_header,
                                                  extra_row=extra_row, *args,
                                                  **kwargs)
        kwargs["align"] = align
        table_builder.set_highlight(highlight)
        self.add(table_builder.create_table(*args, **kwargs))
        self.add_blank_space(margins)

    def add_object_table(self, objs, cols, expand=False, width=0,
                         style=TABLE_STYLE, margins=DEFAULT_MARGIN,
                         extra_row=None, align=flowables.CENTER,
                         table_line=TABLE_LINE, highlight=tables.HIGHLIGHT_ODD,
                         summary_row=None, *args, **kwargs):
        """ Insert an object table. Its parameters are:

        @param objs:       A instance list, where each instance is a table row.
        @type objs:        list.
        @param cols:       A list of ObjectTableColumn, representing the table
                           columns.
        @type cols:        list
        @param expand:     Must be the columns expanded? Defaults to False.
        @type expand:      bool
        @param width:      The table width.
        @type width:       int
        @param style:      The table style.
        @type style:       TableStyle
        @param margins:    How much space before and after the table?
        @type margins:     int/float
        @param extra_row:  An list of strings to be inserted right after
                           the table. This data is included on the report as
                           a normal data table after this object table.
        @type extra_row:   list
        @param align:      The table alignment.
        @type align:       One of LEFT, RIGHT or CENTER
        @param table_line: Define the type of the line that is inserted between
                           the table rows.
        @type table_line:  One of TABLE_LINE or TABLE_LINE_BLANK constants.
        @param highlight:  Sets the table highlight type.
        @type highight:    One of HIGHLIGHT_ODD, HIGHLIGHT_NEVER or HIGHLIGHT_ODD
                           constants defined on stoqlib reporting tables module.
        """
        assert not (expand and width), \
            'Use only expand _OR_ only width at once'
        if expand:
            width = self.get_usable_width()
        self.add_blank_space(margins)
        table_builder = tables.ObjectTableBuilder(objs, cols, style,
                                                  width=width,
                                                  extra_row=extra_row,
                                                  table_line=table_line,
                                                  summary_row=summary_row)
        kwargs["align"] = align
        table_builder.set_highlight(highlight)
        self.add(table_builder.create_table(*args, **kwargs))
        self.add_blank_space(margins)

    def add_grouping_table(self, objs, column_groups, column_widths,
                           header=None, style=TABLE_STYLE,
                           margins=DEFAULT_MARGIN, align=flowables.CENTER,
                           extra_row=None, *args, **kwargs):
        """ TODO """
        # We need to set the table header directly for GroupingTableBuilder
        # because the Columns used with it does not have a name. Note that we
        # have one header for each column width defined and you can use a false
        # value (None, '', 0) to make the previous header span over it.
        self.add_blank_space(margins)
        table_builder = tables.GroupingTableBuilder(objs, column_groups,
                                                    column_widths,
                                                    style=style,
                                                    header=header,
                                                    extra_row=extra_row)
        kwargs["align"] = align
        self.add(table_builder.create_table(*args, **kwargs))
        self.add_blank_space(margins)

    def add_data_table(self, data, style=TABLE_STYLE, margins=DEFAULT_MARGIN,
                       align=flowables.LEFT, *args, **kwargs):
        """ Insert a data table on the report.
        @param data:    The data list. It is composed of list of a lists, where
                        each nested list represents a row. Note that the nested
                        lists must have all the same length.
        @type data:     list
        @param style:   The table style.
        @type style:    TableStyle
        @param margins: How much space before and after the table?
        @type margins:  float/int
        @param align:   The table alignment. One of LEFT, RIGHT, CENTER
                        constants defined on stoqlib reporting flowables module.
        @type align:    One of LEFT, RIGHT or CENTER
        """
        self.add_blank_space(margins)
        table_builder = tables.DataTableBuilder(data, style)
        kwargs["align"] = align
        self.add(table_builder.create_table(*args, **kwargs))
        self.add_blank_space(margins)

    #
    # Reportlab Handlers
    #

    def paint_page_canvas(self, canvas, doc):
        """ This method is called by Reportlab on each time that a page starts
        be drawed.
        """
        if self._do_header:
            self.draw_header(canvas)
        if self._do_footer:
            self.draw_footer(canvas)

    #
    # Hooks
    #

    def draw_header(self, canvas):
        """ Hook called on report header drawing time. """
        raise NotImplementedError

    def draw_footer(self, canvas):
        """ Hook called on report footer drawing time. """
        raise NotImplementedError
