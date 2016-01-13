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

import gio
import gtk
import pango
import poppler

from stoqlib.gui.base.dialogs import get_current_toplevel
from stoqlib.gui.events import PrintReportEvent
from stoqlib.lib.message import warning
from stoqlib.lib.osutils import get_application_dir
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


# https://github.com/Kozea/WeasyPrint/issues/130
# http://pythonhosted.org/cairocffi/cffi_api.html#converting-pycairo-wrappers-to-cairocffi
def _UNSAFE_pycairo_context_to_cairocffi(pycairo_context):
    import cairocffi
    # Sanity check. Continuing with another type would probably segfault.
    if not isinstance(pycairo_context, gtk.gdk.CairoContext):
        raise TypeError('Expected a cairo.Context, got %r' % pycairo_context)

    # On CPython, id() gives the memory address of a Python object.
    # pycairo implements Context as a C struct:
    #     typedef struct {
    #         PyObject_HEAD
    #         cairo_t *ctx;
    #         PyObject *base;
    #     } PycairoContext;
    # Still on CPython, object.__basicsize__ is the size of PyObject_HEAD,
    # ie. the offset to the ctx field.
    # ffi.cast() converts the integer address to a cairo_t** pointer.
    # [0] dereferences that pointer, ie. read the ctx field.
    # The result is a cairo_t* pointer that cairocffi can use.
    return cairocffi.Context._from_pointer(
        cairocffi.ffi.cast('cairo_t **',
                           id(pycairo_context) + object.__basicsize__)[0],
        incref=True)


class PrintOperation(gtk.PrintOperation):
    def __init__(self, report):
        gtk.PrintOperation.__init__(self)
        self.connect("begin-print", self._on_operation_begin_print)
        self.connect("draw-page", self._on_operation_draw_page)
        self.connect("done", self._on_operation_done)
        self.connect("paginate", self._on_operation_paginate)
        self.connect("status-changed", self._on_operation_status_changed)

        self._in_nested_main_loop = False
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
        # GtkPrintOperation.run() is not blocking by default, as the rendering
        # is threaded we need to wait for the operation to finish before we can
        # return from here, since currently the rendering depends on state that
        # might be released just after exiting this function.
        if self._threaded:
            self._in_nested_main_loop = True
            # Before creating a nested main loop, we need to process everything
            # that was pending on the main one as even the PrintOperation may
            # be waiting at this point.
            while gtk.events_pending():
                gtk.main_iteration()
            gtk.main()
            self._in_nested_main_loop = False

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

    def _is_rendering_finished(self):
        return self.get_status() in [
            gtk.PRINT_STATUS_SENDING_DATA,
            gtk.PRINT_STATUS_FINISHED,
            gtk.PRINT_STATUS_FINISHED_ABORTED]

    # Callbacks

    def _on_operation_status_changed(self, operation):
        if (self._in_nested_main_loop and
            self._is_rendering_finished()):
            gtk.main_quit()

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
        # FIXME: This is an specific fix for boleto printing in landscape
        # orientation. We should find a better fix for it or simply remove
        # PrintOperationPoppler when migrating the last reports using
        # reportlab to weasyprint
        if getattr(self._report, 'print_as_landscape', False):
            default_page_setup = gtk.PageSetup()
            default_page_setup.set_orientation(gtk.PAGE_ORIENTATION_LANDSCAPE)
            self.set_default_page_setup(default_page_setup)

        self._report.save()
        uri = gio.File(path=self._report.filename).get_uri()
        self._document = poppler.document_new_from_file(uri, password="")

    def render_done(self):
        self.set_n_pages(self._document.get_n_pages())

    def draw_page(self, cr, page_no):
        page = self._document.get_page(page_no)
        page.render_for_printing(cr)

    def done(self):
        if not os.path.isfile(self._report.filename):
            return
        os.unlink(self._report.filename)


class PrintOperationWEasyPrint(PrintOperation):

    PRINT_CSS_TEMPLATE = """
    @page {
      size: ${ page_width }mm ${ page_height }mm;
      font-family: "${ font_family }";
    }

    body {
      font-family: "${ font_family }";
      font-size: ${ font_size }pt;
    }
    """

    page_setup_name = 'page_setup.ini'
    print_settings_name = 'print_settings.ini'

    def __init__(self, report):
        PrintOperation.__init__(self, report)
        self._load_settings()

        self.connect('create-custom-widget',
                     self._on_operation_create_custom_widget)

        self.set_embed_page_setup(True)
        self.set_use_full_page(True)
        self.set_custom_tab_label(_('Stoq'))

    def _load_settings(self):
        self.config_dir = get_application_dir('stoq')

        settings = gtk.PrintSettings()
        filename = os.path.join(self.config_dir, self.print_settings_name)
        if os.path.exists(filename):
            settings.load_file(filename)
        self.set_print_settings(settings)

        default_page_setup = gtk.PageSetup()
        default_page_setup.set_orientation(gtk.PAGE_ORIENTATION_PORTRAIT)
        filename = os.path.join(self.config_dir, self.page_setup_name)
        if os.path.exists(filename):
            default_page_setup.load_file(filename)
        self.set_default_page_setup(default_page_setup)

    def begin_print(self):
        self._fetch_settings()

    def render(self):
        self._document = self._report.render(
            stylesheet=self.print_css)

    def render_done(self):
        self.set_n_pages(len(self._document.pages))

    def draw_page(self, cr, page_no):
        import weasyprint
        weasyprint_version = tuple(map(int, weasyprint.__version__.split('.')))
        if weasyprint_version >= (0, 18):
            cr = _UNSAFE_pycairo_context_to_cairocffi(cr)
        # 0.75 is here because its also in weasyprint render_pdf()
        self._document.pages[page_no].paint(cr, scale=0.75)

    # Private

    def _fetch_settings(self):
        font_name = self.font_button.get_font_name()

        settings = self.get_print_settings()
        settings.set('stoq-font-name', font_name)
        settings.to_file(os.path.join(self.config_dir, self.print_settings_name))

        page_setup = self.get_default_page_setup()
        page_setup.to_file(os.path.join(self.config_dir, self.page_setup_name))
        orientation = page_setup.get_orientation()

        paper_size = page_setup.get_paper_size()
        width = paper_size.get_width(gtk.UNIT_MM)
        height = paper_size.get_height(gtk.UNIT_MM)
        if orientation in (gtk.PAGE_ORIENTATION_LANDSCAPE,
                           gtk.PAGE_ORIENTATION_REVERSE_LANDSCAPE):
            width, height = height, width

        descr = pango.FontDescription(font_name)

        # CSS expects fonts in pt, get_font_size() is scaled,
        # for screen display pango.SCALE should be used, it looks
        # okay for printed media again, since we're multiplying
        # with 0.75 at the easyprint level as well. At some point
        # we should probably align them.
        font_size = descr.get_size() / pango.SCALE
        self.print_css = render_template_string(
            self.PRINT_CSS_TEMPLATE,
            page_width=width,
            page_height=height,
            font_family=descr.get_family(),
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

        settings = self.get_print_settings()
        font_name = settings.get('stoq-font-name')

        self.font_button = gtk.FontButton(font_name)
        table.attach(self.font_button, 1, 2, 0, 1,
                     xoptions=0,
                     yoptions=0)
        box.pack_start(table, False, False)
        box.show_all()
        return box

    # Callbacks

    def _on_operation_create_custom_widget(self, operation):
        return self._create_custom_tab()


def describe_search_filters_for_reports(filters, **kwargs):
    filter_strings = []
    for filter in filters:
        description = filter.get_description()
        if description:
            filter_strings.append(description)

    kwargs['filter_strings'] = filter_strings
    return kwargs


def print_report(report_class, *args, **kwargs):
    rv = PrintReportEvent.emit(report_class, *args, **kwargs)
    if rv:
        return rv

    filters = kwargs.pop('filters', None)
    if filters:
        kwargs = describe_search_filters_for_reports(filters, **kwargs)

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
        op.set_threaded()
    else:
        op = PrintOperationPoppler(report)

    rv = op.run()
    return rv


def print_labels(label_data, store, purchase=None, receiving=None):
    path = sysparam.get_string('LABEL_TEMPLATE_PATH')
    if path and os.path.exists(path):
        if purchase:
            print_report(LabelReport, purchase.get_data_for_labels(),
                         label_data.skip, store=store)
        elif receiving:
            data = []
            for purchase in receiving.purchase_orders:
                data.extend(purchase.get_data_for_labels())
            print_report(LabelReport, data, label_data.skip, store=store)
        else:
            print_report(LabelReport, [label_data], label_data.skip, store=store)
    else:
        warning(_("It was not possible to print the labels. The "
                  "template file was not found."))
