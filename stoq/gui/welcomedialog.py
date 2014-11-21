# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2011-2012 Async Open Source
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

import locale
import platform

from kiwi.environ import environ
import gtk

from stoqlib.api import api
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.utils.openbrowser import open_browser
from stoqlib.lib.translation import stoqlib_gettext as _


class WelcomeDialog(BasicDialog):
    title = _("Welcome to Stoq")
    size = (800, 400)

    def __init__(self):
        BasicDialog.__init__(self, title=self.title, size=self.size)
        self.toplevel.set_deletable(False)

        self._build_ui()
        self._setup_buttons()
        self.toplevel.connect('map-event', self._on_toplevel__map_event)

    def _on_toplevel__map_event(self, window, event):
        # Load the URI here, since it's after run_dialog is called,
        # otherwise there's no possiblity to hide the dialog if
        # webkit isn't available
        uri = self.get_uri()
        self._open_uri(uri)

    def _build_ui(self):
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.vbox.remove(self.main)
        self.vbox.add(sw)
        sw.show()

        if platform.system() != 'Windows':
            import webkit
            self._view = webkit.WebView()
            self._view.connect(
                'navigation-policy-decision-requested',
                self._on_view__navigation_policy_decision_requested)
            sw.add(self._view)
            self._view.show()
        else:
            self._view = None

    def _setup_buttons(self):
        self.cancel_button.hide()
        self.ok_button.set_label(_("_Start using Stoq"))

    def _open_uri(self, uri):
        if self._view:
            self._view.load_uri(uri)
            self.ok_button.grab_focus()
        else:
            open_browser(uri, self.toplevel.get_screen())
            self.toplevel.hide()

    def get_uri(self):
        # Make sure we extract everything from html in case we are running
        # from an egg
        environ.get_resource_filename('stoq', 'html')

        if locale.getlocale()[0] == 'pt_BR' or platform.system() == 'Windows':
            content = environ.get_resource_filename('stoq', 'html',
                                                    'welcome-pt_BR.html')
        else:
            content = environ.get_resource_filename('stoq', 'html',
                                                    'welcome.html')
        if api.sysparam.get_bool('DEMO_MODE'):
            content += '?demo-mode'
        return 'file:///' + content

    def _on_view__navigation_policy_decision_requested(self, view, frame,
                                                       request, action,
                                                       policy):
        uri = request.props.uri
        if not uri.startswith('file:///'):
            policy.ignore()
            open_browser(uri, self.toplevel.get_screen())
