# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2012 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Crash report dialog """

import logging

from gi.repository import Gtk
from gi.repository import GObject
from stoqlib.lib.component import get_utility
from kiwi.ui.dialogs import HIGAlertDialog
from kiwi.utils import gsignal

from stoq.lib.gui.base.dialogs import get_current_toplevel
from stoqlib.api import api
from stoqlib.lib.crashreport import collect_report
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.threadutils import schedule_in_main_thread
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.webservice import WebService

_ = stoqlib_gettext

_DEFAULT_COMMENT = _("Add a comment (comments are not publicly visible)")
_DEFAULT_EMAIL = _("Enter your email address here")
_N_TRIES = 3

logger = logging.getLogger(__name__)


class ReportSubmitter(GObject.GObject):
    gsignal('failed', object)
    gsignal('submitted', object)

    def __init__(self):
        GObject.GObject.__init__(self)

        self._count = 0
        self._api = WebService()
        self.report = collect_report()

    def _done(self, args):
        self.emit('submitted', args)

    def _error(self, args):
        self.emit('failed', args)

    def submit(self):
        return self._api.bug_report(self.report,
                                    callback=self._on_report__callback,
                                    errback=self._on_report__errback)

    def _on_report__callback(self, response):
        if response.status_code == 200:
            self._on_success(response.json())
        else:
            self._on_error()

    def _on_report__errback(self, failure):
        self._on_error(failure)

    def _on_error(self, data=None):
        logger.info('Failed to report bug: %r count=%d' % (data, self._count))
        if self._count < _N_TRIES:
            self.submit()
        else:
            schedule_in_main_thread(self.emit, 'failed', data)
        self._count += 1

    def _on_success(self, data):
        logger.info('Finished sending bugreport: %r' % (data, ))
        schedule_in_main_thread(self.emit, 'submitted', data)


class CrashReportDialog(object):
    def __init__(self, parent, callback):
        self._parent = parent
        self._report_submitter = ReportSubmitter()
        self._report_submitter.connect('submitted',
                                       self._on_report__submitted)
        self._report_submitter.connect('failed',
                                       self._on_report__failed)
        self._create_dialog()
        self.submitted = False
        self._callback = callback

    def _create_dialog(self):
        app_info = get_utility(IAppInfo, None)

        self._dialog = HIGAlertDialog(parent=self._parent,
                                      flags=Gtk.DialogFlags.MODAL,
                                      type=Gtk.MessageType.WARNING)

        self._dialog.set_details_label(_("Details ..."))
        self._dialog.set_resizable(True)
        primary_fmt = _('We\'r sorry to inform you that an error occurred while '
                        'running %s. Please help us improving Stoq by sending a '
                        'automatically generated report about the incident.\n'
                        'Click on details to see the report text.')
        self._dialog.set_primary(primary_fmt % (app_info.get('name'), ),
                                 bold=False)

        self._create_details()
        self._create_comments()
        self._create_email()

        self._no_button = self._dialog.add_button(_('No thanks'),
                                                  Gtk.ResponseType.NO)
        self._yes_button = self._dialog.add_button(_('Send report'),
                                                   Gtk.ResponseType.YES)

        self._insert_tracebacks()

    def _create_details(self):
        sw = Gtk.ScrolledWindow()
        # FIXME: The overlay scrolling when a TextView is inside a
        # ScrolledWindow is somewhat broken in a way that it would make it get
        # a height of 0 when being displayed.
        sw.set_property('overlay_scrolling', False)
        self._dialog.set_details_widget(sw)
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        sw.show()

        view = Gtk.TextView()
        sw.add(view)
        sw.set_size_request(500, 350)
        view.show()
        self._details_buffer = view.get_buffer()

    def _create_comments(self):
        sw = Gtk.ScrolledWindow()
        # FIXME: The overlay scrolling when a TextView is inside a
        # ScrolledWindow is somewhat broken in a way that it would make it get
        # a height of 0 when being displayed.
        sw.set_property('overlay_scrolling', False)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._dialog.main_vbox.pack_start(sw, True, True, 6)
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        sw.show()

        view = Gtk.TextView()
        view.set_wrap_mode(Gtk.WrapMode.WORD)
        view.set_accepts_tab(False)
        sc = view.get_style_context()

        def focus_in(view, event):
            if self._comments_buffer.props.text != _DEFAULT_COMMENT:
                return
            self._comments_buffer.set_text("")
            sc.remove_class('visualmode')
        view.connect('focus-in-event', focus_in)

        def focus_out(view, event):
            if self._comments_buffer.props.text:
                return
            self._comments_buffer.set_text(_DEFAULT_COMMENT)
            sc.add_class('visualmode')

        view.connect('focus-out-event', focus_out)
        view.set_size_request(-1, 100)
        sw.add(view)
        self._comments_buffer = view.get_buffer()
        self._comments_buffer.create_tag("highlight")
        self._comments_buffer.insert_with_tags_by_name(
            self._comments_buffer.get_iter_at_offset(0), _DEFAULT_COMMENT,
            'highlight')
        sc.add_class('visualmode')
        view.show()
        self._comments_view = view

    def _create_email(self):
        self._email_entry = Gtk.Entry()
        self._email_entry.set_placeholder_text(_DEFAULT_EMAIL)
        self._dialog.main_vbox.pack_start(self._email_entry, False, False, 6)
        self._email_entry.show()

    def _insert_tracebacks(self):
        report = self._report_submitter.report
        lines = [report.get('log', '')]
        for key in sorted(report):
            # Tracebacks already apear in the log
            if key in ('tracebacks', 'log'):
                continue
            lines.append('%s: %s' % (key, report[key]))

        self._details_buffer.set_text("\n".join(lines))

    def _finish(self):
        self._dialog.set_primary(
            _("Thanks for submitting the crash report!\n"
              "We will use it to make Stoq a better software."),
            bold=False)
        self._yes_button.set_label(_("Close"))
        self._comments_view.set_sensitive(False)
        self._email_entry.set_sensitive(False)
        self._yes_button.set_sensitive(True)

    def _show_report(self, data):
        message = data.get('message')
        if message is not None:
            if data.get('report-url'):
                label = Gtk.LinkButton(data['report-url'], message)
            else:
                label = Gtk.Label(label=message)
            self._dialog.vbox.pack_start(label, True, True, 0)
            label.show()
        self._finish()

    def _show_error(self):
        label = Gtk.Label(label=_("Failed to submit bugreport"))
        self._dialog.vbox.pack_start(label, True, True, 0)
        label.show()
        self._finish()

    def _submit_report(self):
        self._no_button.hide()
        self._yes_button.set_sensitive(False)
        self._yes_button.set_label(_('Sending...'))
        if self._parent:
            self._parent.destroy()

        comments = self._comments_buffer.props.text
        if comments == _DEFAULT_COMMENT:
            comments = ""
        self._report_submitter.report['comments'] = comments
        email = self._email_entry.get_text()
        if email == _DEFAULT_EMAIL:
            email = ""
        self._report_submitter.report['email'] = email
        self._report_submitter.submit()

    def _on_dialog__response(self, dialog, response):
        if response == Gtk.ResponseType.YES:
            if self.submitted:
                self._destroy()

            self._submit_report()
            return

        self._destroy()

    def _destroy(self):
        self._dialog.destroy()
        if self._callback is not None:
            self._callback()

    def run(self):
        self._dialog.connect('response', self._on_dialog__response)
        self._dialog.show_all()

    def _on_report__failed(self, response, failure):
        self._show_error()
        self.submitted = True

    def _on_report__submitted(self, response, data):
        # If the requested successed but the script failed, data is None.
        if not data:
            self._show_error()
        else:
            self._show_report(data)
        self.submitted = True


def show_dialog(callback=None):
    """Show a crash report dialog
    """
    parent = get_current_toplevel()
    crd = CrashReportDialog(parent, callback=callback)
    return crd.run()


if __name__ == '__main__':   # pragma: no cover
    ec = api.prepare_test()
    show_dialog(callback=Gtk.main_quit)
    Gtk.main()
