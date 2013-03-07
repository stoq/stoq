# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source
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

import logging
import os
import platform
import tempfile
import threading
import poppler

import gio
import gtk

from stoqlib.gui.base.dialogs import get_current_toplevel
from stoqlib.lib.message import warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.template import render_template_string
from stoqlib.lib.threadutils import (schedule_in_main_thread,
                                     terminate_thread)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.report import HTMLReport
from stoqlib.reporting.labelreport import LabelReport


_ = stoqlib_gettext
_system = platform.system()
log = logging.Logger(__name__)


class PrintOperation(gtk.PrintOperation):
    def __init__(self, report):
        gtk.PrintOperation.__init__(self)
        self.connect("begin-print", self._on_operation_begin_print)
        self.connect("draw-page", self._on_operation_draw_page)
        self.connect("done", self._on_operation_done)
        self.connect("paginate", self._on_operation_paginate)
        self.connect("status-changed", self._on_operation_status_changed)

        self._threaded = False
        self._printing_complete = False
        self._report = report
        self._rendering_thread = None

        self.set_job_name(self._report.title)
        self.set_show_progress(True)
        self.set_track_print_status(True)

    # Public API

    def set_threaded(self):
        self._threaded = True
        self.set_allow_async(True)

    def run(self):
        gtk.PrintOperation.run(self,
                               gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG,
                               parent=get_current_toplevel())

    def begin_print(self):
        """This is called before printing is done.
        It can be used to fetch print settings that the user
        selected in the dialog
        """

    def render(self):
        """Renders the actual page.
        This might run in a separate thread, no glib/gtk+ calls are allowed
        here, they needs to be done in render_done() which is called when
        this is finished.
        """
        raise NotImplementedError

    def render_done(self):
        """Rendering of the printed page is done. This should call
        self.set_n_pages()
        """
        raise NotImplementedError

    def draw_page(self, cr, page_no):
        """Draws a page
        :param cr: a cairo context
        :param int page_no: the page to draw
        """
        raise NotImplementedError

    def done(self):
        """Called when rendering and drawing is complete,
        can be used to free resources created during printing.
        """

    # Private API

    def _threaded_render(self):
        self.render()
        schedule_in_main_thread(self._threaded_render_done)

    def _threaded_render_done(self):
        if self.get_status() == gtk.PRINT_STATUS_FINISHED_ABORTED:
            return
        self.render_done()
        self._printing_complete = True

    # Callbacks

    def _on_operation_status_changed(self, operation):
        if self.get_status() == gtk.PRINT_STATUS_FINISHED_ABORTED:
            terminate_thread(self._rendering_thread)

    def _on_operation_begin_print(self, operation, context):
        self.begin_print()
        if self._threaded:
            self._rendering_thread = threading.Thread(target=self._threaded_render)
            self._rendering_thread.start()
        else:
            self.render()
            self.render_done()
            self._printing_complete = True

    def _on_operation_paginate(self, operation, context):
        return self._printing_complete

    def _on_operation_draw_page(self, operation, context, page_no):
        cr = context.get_cairo_context()
        self.draw_page(cr, page_no)

    def _on_operation_done(self, operation, context):
        self.done()


class PrintOperationPoppler(PrintOperation):

    def render(self):
        self._report.save()
        uri = gio.File(path=self._report.filename).get_uri()
        self._document = poppler.document_new_from_file(uri, password="")

    def render_done(self):
        self.set_n_pages(self._document.get_n_pages())

    def draw_page(self, cr, page_no):
        page = self._document.get_page(page_no)
        page.render_for_printing(cr)

    def done(self):
        os.unlink(self._report.filename)


class PrintOperationWEasyPrint(PrintOperation):

    PRINT_CSS_TEMPLATE = """
    @page {
      size: ${ page_width }mm ${ page_height }mm;
      font-family: ${ font_family };
    }

    body {
      font-family: ${ font_family };
      font-size: ${ font_size }pt;
    }
    """

    def __init__(self, report):
        PrintOperation.__init__(self, report)
        self.connect('create-custom-widget',
                     self._on_operation_create_custom_widget)

        self.set_embed_page_setup(True)
        self.set_use_full_page(True)
        self.set_custom_tab_label(_('Stoq'))

    def begin_print(self):
        self._fetch_settings()

    def render(self):
        self._document = self._report.render(
            stylesheet=self.print_css)

    def render_done(self):
        self.set_n_pages(len(self._document.pages))

    def draw_page(self, cr, page_no):
        # 0.75 is here because its also in weasyprint render_pdf()
        self._document.pages[page_no].paint(cr, scale=0.75)

    # Private

    def _fetch_settings(self):
        page_setup = self.get_default_page_setup()
        orientation = page_setup.get_orientation()

        paper_size = page_setup.get_paper_size()
        width = paper_size.get_width(gtk.UNIT_MM)
        height = paper_size.get_height(gtk.UNIT_MM)
        if orientation in (gtk.PAGE_ORIENTATION_LANDSCAPE,
                           gtk.PAGE_ORIENTATION_REVERSE_LANDSCAPE):
            width, height = height, width
        # FIXME: Doesn't work if you select any options, need to use
        #        PangoFontDescription or so to correct this, like this:
        # >>> pango.FontDescription('Sans Serif Italic').get_style()
        # <enum PANGO_STYLE_ITALIC of type PangoStyle>
        # >>> pango.FontDescription('Sans Serif Italic').get_family()
        # 'Sans Serif'
        # >>> pango.FontDescription('Ubuntu Italic 12').get_family()
        # 'Ubuntu'
        # >>> pango.FontDescription('Ubuntu Italic 12').get_size()
        # 12288
        # >>> pango.FontDescription('Ubuntu Italic 12').get_size()
        font = self.font_button.get_font_name()
        font_size = font.split(' ')[-1]
        font_family = font[:-len(font_size)]

        self.print_css = render_template_string(
            self.PRINT_CSS_TEMPLATE,
            page_width=width,
            page_height=height,
            font_family=font_family,
            font_size=font_size)

    def _create_custom_tab(self):
        # TODO: Improve this code (maybe a slave)
        box = gtk.VBox()
        table = gtk.Table()
        table.set_row_spacings(6)
        table.set_col_spacings(6)
        table.set_border_width(6)
        table.attach(gtk.Label(_('Font:')), 0, 1, 0, 1,
                     yoptions=0,
                     xoptions=0)
        self.font_button = gtk.FontButton()
        table.attach(self.font_button, 1, 2, 0, 1,
                     xoptions=0,
                     yoptions=0)
        box.pack_start(table, False, False)
        box.show_all()
        return box

    # Callbacks

    def _on_operation_create_custom_widget(self, operation):
        return self._create_custom_tab()


def describe_search_filters_for_reports(**kwargs):
    filters = kwargs.pop('filters')
    filter_strings = []
    for filter in filters:
        description = filter.get_description()
        if description:
            filter_strings.append(description)

    kwargs['filter_strings'] = filter_strings
    return kwargs


def print_report(report_class, *args, **kwargs):
    if kwargs.get('filters'):
        kwargs = describe_search_filters_for_reports(**kwargs)

    tmp = tempfile.mktemp(suffix='.pdf', prefix='stoqlib-reporting')
    report = report_class(tmp, *args, **kwargs)
    report.filename = tmp
    if _system == "Windows":
        report.save()
        log.info("Starting PDF reader for %r" % (report.filename, ))
        # Simply execute the file
        os.startfile(report.filename)
        return

    if isinstance(report, HTMLReport):
        op = PrintOperationWEasyPrint(report)
    else:
        op = PrintOperationPoppler(report)

    op.set_threaded()
    rv = op.run()
    return rv


def print_labels(label_data, store, purchase=None):
    param = sysparam(store).LABEL_TEMPLATE_PATH
    if param and param.path and os.path.exists(param.path):
        if purchase:
            print_report(LabelReport, purchase.get_data_for_labels(),
                         label_data.skip, store=store)
        else:
            print_report(LabelReport, [label_data], label_data.skip, store=store)
    else:
        warning(_("It was not possible to print the labels. The "
                  "template file was not found."))
