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

# When running this file we need to explicitly say that we want to use
# the gtk2reactor, otherwise the poll reactor will be installed when
# t.i.reactor is first accessed/used.
if __name__ == '__main__':  # pragma: no cover
    from stoqlib.net import gtk2reactor
    gtk2reactor.install()

import os

import gtk
from kiwi.component import get_utility
from kiwi.ui.dialogs import HIGAlertDialog
from twisted.internet import defer, reactor

from stoqlib.api import api
from stoqlib.gui.base.dialogs import get_current_toplevel
from stoqlib.gui.widgets.hintedentry import HintedEntry
from stoqlib.lib.crashreport import ReportSubmitter
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

_DEFAULT_COMMENT = _("Add a comment (comments are not publicly visible)")
_DEFAULT_EMAIL = _("Enter your email address here")
_N_TRIES = 3


class CrashReportDialog(object):
    def __init__(self, parent):
        self._parent = parent
        self._report_submitter = ReportSubmitter()
        self._report_submitter.connect('submitted',
                                       self._on_report__submitted)
        self._report_submitter.connect('failed',
                                       self._on_report__failed)
        self._create_dialog()
        self.submitted = False
        self.deferred = defer.Deferred()

    def _create_dialog(self):
        app_info = get_utility(IAppInfo, None)

        self._dialog = HIGAlertDialog(parent=self._parent,
                                      flags=gtk.DIALOG_MODAL,
                                      type=gtk.MESSAGE_WARNING)

        self._dialog.set_details_label(_("Details ..."))
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
                                                  gtk.RESPONSE_NO)
        self._yes_button = self._dialog.add_button(_('Send report'),
                                                   gtk.RESPONSE_YES)

        self._insert_tracebacks()

    def _create_details(self):
        sw = gtk.ScrolledWindow()
        self._dialog.set_details_widget(sw)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        sw.show()

        view = gtk.TextView()
        sw.add(view)
        view.set_size_request(500, 350)
        view.show()
        self._details_buffer = view.get_buffer()

    def _create_comments(self):
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._dialog.main_vbox.pack_start(sw, False, False, 6)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        sw.show()

        view = gtk.TextView()
        view.set_wrap_mode(gtk.WRAP_WORD)
        view.set_accepts_tab(False)
        view_style = view.get_style()

        def focus_in(view, event):
            if self._comments_buffer.props.text != _DEFAULT_COMMENT:
                return
            self._comments_buffer.set_text("")
            view.modify_text(
                gtk.STATE_NORMAL, view_style.text[gtk.STATE_NORMAL])
        view.connect('focus-in-event', focus_in)

        def focus_out(view, event):
            if self._comments_buffer.props.text:
                return
            self._comments_buffer.set_text(_DEFAULT_COMMENT)
            view.modify_text(
                gtk.STATE_NORMAL, view_style.text[gtk.STATE_INSENSITIVE])

        view.connect('focus-out-event', focus_out)
        view.set_size_request(-1, 100)
        sw.add(view)
        self._comments_buffer = view.get_buffer()
        self._comments_buffer.create_tag("highlight")
        self._comments_buffer.insert_with_tags_by_name(
            self._comments_buffer.get_iter_at_offset(0), _DEFAULT_COMMENT,
            'highlight')
        view.modify_text(
            gtk.STATE_NORMAL, view_style.text[gtk.STATE_INSENSITIVE])
        view.show()
        self._comments_view = view

    def _create_email(self):
        self._email_entry = HintedEntry()
        self._email_entry.set_hint(_DEFAULT_EMAIL)
        self._email_entry.show_hint()
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
                label = gtk.LinkButton(data['report-url'], message)
            else:
                label = gtk.Label(message)
            self._dialog.vbox.pack_start(label)
            label.show()
        self._finish()

    def _show_error(self):
        label = gtk.Label(_("Failed to submit bugreport"))
        self._dialog.vbox.pack_start(label)
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
        if response == gtk.RESPONSE_YES:
            if self.submitted:
                self._destroy()

            self._submit_report()
            return

        self._destroy()

    def _destroy(self):
        self._dialog.destroy()
        self.deferred.callback(None)

    def run(self):
        self._dialog.connect('response', self._on_dialog__response)
        self._dialog.show_all()
        return self.deferred

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


def show_dialog(interactive=True):
    """Show a crash report dialog
    """
    parent = get_current_toplevel()
    crd = CrashReportDialog(parent)
    return crd.run()


if __name__ == '__main__':   # pragma: no cover
    ec = api.prepare_test()
    d = show_dialog()

    def cb(*args):
        os._exit(0)
    d.addCallback(cb)
    reactor.run()
