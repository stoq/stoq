# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2011 Async Open Source
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

import gettext
import locale
import platform

from kiwi.environ import environ
import gtk

from stoqlib.api import api
from stoqlib.gui.openbrowser import open_browser

_ = gettext.gettext


class WelcomeDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self)
        self.set_size_request(800, 480)
        self.set_deletable(False)

        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.get_content_area().pack_start(sw)

        if platform.system() == 'Windows':
            return
        import webkit
        self._view = webkit.WebView()
        self._view.connect(
            'navigation-policy-decision-requested',
            self._on_view__navigation_policy_decision_requested)
        sw.add(self._view)

        self.button = self.add_button(_("_Start using Stoq"), gtk.RESPONSE_OK)

        self.set_title(_("Welcome to Stoq"))
        self.show_all()

    def get_uri(self):
        if locale.getlocale()[0] == 'pt_BR' or platform.system() == 'Windows':
            content = environ.find_resource('html', 'welcome-pt_BR.html')
        else:
            content = environ.find_resource('html', 'welcome.html')
        if api.sysparam(api.get_connection()).DEMO_MODE:
            content += '?demo-mode'
        return 'file:///' + content

    def run(self):
        uri = self.get_uri()
        if platform.system() == 'Windows':
            open_browser(uri, self.get_screen())
            return
        self._view.load_uri(uri)
        self.button.grab_focus()
        return super(WelcomeDialog, self).run()

    def _on_view__navigation_policy_decision_requested(self, view, frame,
                                                       request, action,
                                                       policy):
        uri = request.props.uri
        if not uri.startswith('file:///'):
            policy.ignore()
            open_browser(uri, self.get_screen())
