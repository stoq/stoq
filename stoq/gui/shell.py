# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import gettext
import logging

from twisted.internet import reactor
from stoqlib.exceptions import LoginError
from stoqlib.lib.message import error

from stoq.gui.runner import ApplicationRunner

_ = gettext.gettext
log = logging.getLogger('stoq.shell')
PRIVACY_STRING = _(
    "One of the new features of Stoq 1.0 is support for online "
    "services. Features using the online services include automatic "
    "bug report and update notifications. More services are under development."
    "To be able to provide a better service and properly identify the user "
    "we will collect the CNPJ of the primary branch and the ip address.\n\n"
    "<b>We will not disclose the collected information and we are committed "
    "to keeping your privacy intact.</b>")


class Shell(object):
    def __init__(self, options, appname=None):
        self.options = options
        self.appname = appname
        self.runner = ApplicationRunner(options)
        self.ran_wizard = False

        self._login()
        self._check_param_main_branch()
        self._check_param_online_services()
        self._maybe_show_welcome_dialog()
        self._run_app(appname)

    def _login(self):
        try:
            if not self.runner.login():
                return
        except LoginError, e:
            error(e)

    def _check_param_main_branch(self):
        from stoqlib.database.runtime import (get_connection, new_transaction,
                                              get_current_station)
        from stoqlib.domain.person import Person
        from stoqlib.domain.interfaces import IBranch, ICompany
        from stoqlib.lib.parameters import sysparam
        conn = get_connection()
        compaines = Person.iselect(ICompany, connection=conn)
        if (compaines.count() == 0 or
            not sysparam(conn).MAIN_COMPANY):
            from stoqlib.gui.base.dialogs import run_dialog
            from stoqlib.gui.dialogs.branchdialog import BranchDialog
            from stoqlib.lib.message import info
            if self.ran_wizard:
                info(_("You need to register a company before start using Stoq"))
            else:
                info(_("Could not find a company. You'll need to register one "
                       "before start using Stoq"))
            trans = new_transaction()
            person = run_dialog(BranchDialog, None, trans)
            if not person:
                raise SystemExit
            branch = IBranch(person)
            sysparam(trans).MAIN_COMPANY = branch.id
            get_current_station(trans).branch = branch
            trans.commit()

    def _check_param_online_services(self):
        from stoqlib.database.runtime import new_transaction
        from stoqlib.lib.parameters import sysparam

        trans = new_transaction()
        sparam = sysparam(trans)
        val = sparam.ONLINE_SERVICES
        if val is None:
            import gtk
            from kiwi.ui.dialogs import HIGAlertDialog
            # FIXME: All of this is to avoid having to set markup as the default
            #        in kiwi/ui/dialogs:HIGAlertDialog.set_details, after 1.0
            #        this can be simplified when we fix so that all descriptions
            #        sent to these dialogs are properly escaped
            dialog = HIGAlertDialog(
                parent=None,
                flags=gtk.DIALOG_MODAL,
                type=gtk.MESSAGE_WARNING)
            dialog.add_button(_("Not right now"), gtk.RESPONSE_NO)
            dialog.add_button(_("Enable online services"), gtk.RESPONSE_YES)

            dialog.set_primary(_('Do you want to enable Stoq online services?'))
            dialog.set_details(PRIVACY_STRING, use_markup=True)
            dialog.set_default_response(gtk.RESPONSE_YES)
            response = dialog.run()
            dialog.destroy()
            sparam.ONLINE_SERVICES = int(bool(response == gtk.RESPONSE_YES))
        trans.commit()

    def _maybe_show_welcome_dialog(self):
        from kiwi.component import get_utility
        from stoqlib.lib.interfaces import IStoqConfig

        config = get_utility(IStoqConfig)
        if config.get('General', 'show_welcome_dialog') == 'False':
            return
        config.set('General', 'show_welcome_dialog', 'False')
        config.flush()

        from stoq.gui.welcomedialog import WelcomeDialog
        from stoqlib.gui.base.dialogs import run_dialog
        run_dialog(WelcomeDialog)

    def _run_app(self, appname):
        from stoq.gui.launcher import Launcher
        launcher = Launcher(self.options, self.runner)
        launcher.show()
        if appname:
            app = self.runner.get_app_by_name(appname)
            self.runner.run(app, launcher)

    def run(self):
        log.debug("Entering reactor")
        if not reactor.running:
            reactor.run()
            log.info("Shutting down application")
