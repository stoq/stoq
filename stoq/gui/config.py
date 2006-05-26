# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Stoq Configuration dialogs"""

import gettext

from kiwi.python import Settable

from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.database import DatabaseSettings
from stoqlib.lib.message import warning


_ = gettext.gettext


#
# Wizard Steps
#


class DatabaseSettingsStep(WizardEditorStep):
    gladefile = 'DatabaseSettingsStep'
    model_type = DatabaseSettings
    proxy_widgets = ('address',
                     'port',
                     'username',
                     'password',
                     'dbname')
    stoq_user_proxy = ('stoq_user_passwd',)

    (TRUST_AUTHENTICATION,
     PASSWORD_AUTHENTICATION) = range(2)

    authentication_types = {TRUST_AUTHENTICATION: _("Trust"),
                            PASSWORD_AUTHENTICATION: _("Needs Password")}

    def __init__(self, wizard, model):
        self.wizard_model = model
        self.authentication_items = None
        WizardEditorStep.__init__(self, None, wizard)
        self.title_label.set_size('xx-large')
        self.title_label.set_bold(True)
        self.title_label.set_color('blue')
        self.hint_label.set_size('small')
        self._update_widgets()

    def _update_widgets(self):
        if not self.authentication_items:
            return
        selected = self.authentication_type.get_selected_data()
        need_password = selected == self.PASSWORD_AUTHENTICATION
        self.password.set_sensitive(need_password)
        self.passwd_label.set_sensitive(need_password)

    #
    # WizardStep hooks
    #

    def create_model(self, conn):
        db_settings = DatabaseSettings()
        self.wizard_model.db_settings = db_settings
        return db_settings

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def validate_step(self):
        if not self.model.check_database_address():
            msg = _("The database address '%s' is invalid. Please fix the "
                    "address you have set and try again"
                    % self.model.address)
            warning(_(u'Invalid database address'), long=msg)
            self.address.set_invalid(_("Invalid database address"))
            self.force_validation()
            return False
        conn_ok, error_msg = self.model.check_database_connection()
        if not conn_ok:
            warning(_('Invalid database settings'), long=error_msg)
            return False
        return True

    def next_step(self):
        # TODO The next step will be implemented on bug 2088
        pass

    def setup_proxies(self):
        items = [(value, key)
                    for key, value in self.authentication_types.items()]
        self.authentication_type.prefill(items)
        self.authentication_items = items
        self.add_proxy(self.model, DatabaseSettingsStep.proxy_widgets)
        self.wizard_model.stoq_user_data = Settable(password='')
        self.add_proxy(self.wizard_model.stoq_user_data,
                       DatabaseSettingsStep.stoq_user_proxy)

    #
    # Callbacks
    #

    def on_authentication_type__content_changed(self, *args):
        self._update_widgets()


#
# Main wizard
#


class FirstTimeConfigWizard(BaseWizard):
    title = _("Setting up Stoq")
    size = (350, 200)

    def __init__(self):
        self.model = Settable(db_settings=None, stoq_user_data=None)
        first_step = DatabaseSettingsStep(self, self.model)
        BaseWizard.__init__(self, None, first_step, self.model,
                            title=self.title)
        # TODO Implement other wizard steps on bug 2088
        self.enable_finish()

    #
    # WizardStep hooks
    #

    def finish(self):
        self.retval = self.model
        self.close()
