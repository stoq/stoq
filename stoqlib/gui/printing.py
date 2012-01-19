# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source
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

import os
import platform
import tempfile

import gio
import gtk

from stoqlib.api import api
from stoqlib.gui.base.dialogs import get_current_toplevel
from stoqlib.exceptions import ReportError
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.base.utils import print_file, print_preview


_ = stoqlib_gettext
_system = platform.system()


def _get_printers_lpstat():
    import commands

    # TODO check also if cups is running or not and give
    # proper messages to users
    func = commands.getoutput
    if not func("lpstat -v"):
        return []
    printers = []
    res = func("lpstat -d").split(":")
    if len(res) > 1:
        printers.append(res[1].strip())
    for p in func('lpstat -a').split('\n'):
        printer_name = p.split()[0].strip()
        if printer_name in printers:
            continue
        printers.append(printer_name)
    return printers


def _get_available_printers():
    if _system == "Linux":
        return _get_printers_lpstat()
    elif _system == "Windows":
        import win32print
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_NAME)
        return [p[1] for p in printers]
    else:
        raise SystemExit("unknown system: %s" % (_system, ))


# FIXME: Remove as soon as poppler is properly tested
try:
    import gtkunixprint
    gtkunixprint # pyflakes
except ImportError:
    gtkunixprint = None


class GtkPrintDialog(object):
    """A dialog to print PDFs using the printer dialog in Gtk+ 2.10+
    """
    def __init__(self, report):
        self._report = report
        self._dialog = self._create_dialog()

    def _create_dialog(self):
        dialog = gtkunixprint.PrintUnixDialog(parent=get_current_toplevel())
        dialog.set_manual_capabilities(gtkunixprint.PRINT_CAPABILITY_COPIES |
                                       gtkunixprint.PRINT_CAPABILITY_PAGE_SET)
        button = self._add_preview_button(dialog)
        button.connect('clicked', self._on_preview_button__clicked)

        # FIXME: Enable before release
        #button = self._add_mailto_button(dialog)
        #button.connect('clicked', self._on_mailto_button__clicked)
        return dialog

    def _add_preview_button(self, dialog):
        # Add a preview button
        button = gtk.Button(stock=gtk.STOCK_PRINT_PREVIEW)
        dialog.action_area.pack_start(button)
        dialog.action_area.reorder_child(button, 0)
        button.show()
        return button

    def _add_mailto_button(self, dialog):
        # Add a mailto button
        button = gtk.Button(label=_('Send PDF by e-mail'))
        dialog.action_area.pack_start(button)
        dialog.action_area.reorder_child(button, 0)
        button.show()
        return button

    def _send_to_printer(self, printer, settings, page_setup):
        job = gtkunixprint.PrintJob(self._report.title, printer,
                                    settings, page_setup)
        job.set_source_file(self._report.filename)
        job.send(self._on_print_job_complete)

    def _print_preview(self):
        print_preview(self._report.filename, keep_file=True)

    def _pdfmailto(self):
        if not os.path.exists(self._report.filename):
            raise OSError("the file does not exist")
        user = api.get_current_user(api.get_connection())
        os.system("/usr/local/bin/pdfmailto %s '%s'" % (
                                self._report.filename, user.person.name))

    #
    # Public API
    #

    def run(self):
        response = self._dialog.run()
        if response in [gtk.RESPONSE_CANCEL,
                        gtk.RESPONSE_DELETE_EVENT]:
            self._dialog.destroy()
            self._dialog = None
        elif response == gtk.RESPONSE_OK:
            self._send_to_printer(self._dialog.get_selected_printer(),
                                  self._dialog.get_settings(),
                                  self._dialog.get_page_setup())
            self._dialog.destroy()
            self._dialog = None
        else:
            raise AssertionError("unhandled response: %d" % (response, ))

    #
    # Callbacks
    #

    def _on_preview_button__clicked(self, button):
        self._print_preview()

    def _on_mailto_button__clicked(self, button):
        self._pdfmailto()

    def _on_print_job_complete(self, job, data, error):
        if error:
            print 'FIXME, handle error:', error


try:
    import poppler
    poppler # pyflakes
except ImportError:
    poppler = None


class GtkPrintOperationDialog(object):
    def __init__(self, report):
        self._report = report

        self._operation = gtk.PrintOperation()
        self._operation.connect("begin-print", self._on_operation_begin_print)
        self._operation.connect("draw-page", self._on_operation_draw_page)
        self._operation.connect("done", self._on_operation_done)
        self._operation.set_show_progress(True)
        self._operation.set_track_print_status(True)

    def _on_operation_begin_print(self, operation, context):
        operation.set_n_pages(self._document.get_n_pages())

    def _on_operation_draw_page(self, operation, context, page_no):
        cr = context.get_cairo_context()
        page = self._document.get_page(page_no)
        page.render_for_printing(cr)

    def _on_operation_done(self, operation, context):
        os.unlink(self._report.filename)

    def run_pdf(self):
        self._operation.set_job_name(self._report.title)
        uri = gio.File(path=self._report.filename).get_uri()
        self._document = poppler.document_new_from_file(uri, password="")
        self._operation.run(gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG,
                            parent=get_current_toplevel())


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
    try:
        report.save()
    except ReportError, e:
        warning(_("Error while printing report"),
                _('Details:') + '\n' + str(e))
        return

    if poppler:
        dialog_class = GtkPrintOperationDialog

    if gtkunixprint:
        dialog_class = GtkPrintDialog

    if _system == "Windows":
        print_file(report.filename)
        return

    dialog = dialog_class(report)
    dialog.run()

    if not poppler:
        os.unlink(report.filename)
