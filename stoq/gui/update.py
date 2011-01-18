# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## Author(s):   George Y. Kussumoto      <george@async.com.br>
##              Ronaldo Maia             <romaia@async.com.br>
##
##
""" Schema Update Wizard """

import gettext
import time
import threading

from zope.interface import implements

import gobject
import gtk

from kiwi.component import get_utility, provide_utility

from stoqlib.database.migration import StoqlibSchemaMigration
from stoqlib.gui.base.wizards import BaseWizard, BaseWizardStep
from stoqlib.lib.interfaces import ISystemNotifier


_ = gettext.gettext

#
# Wizard Steps
#

class UpdateWelcomeStep(BaseWizardStep):
    gladefile = 'UpdateWelcomeStep'

    def post_init(self):
        self.title_label.set_size('xx-large')
        self.title_label.set_bold(True)

    def next_step(self):
        return UpdateSchemaStep(None, self.wizard)


class _MySystemNotifier:
    implements(ISystemNotifier)

    def __init__(self, step):
        self.step = step

    def _msg(self, short, description):
        all = self.step.status_label.get_text() or u''
        self.step.status_label.set_text(all + short + '\n')

    def info(self, short, description):
        self._msg(short, description)

    def yesno(self, text, default=-1, *verbs):
        self._msg(text, '')

    def warning(self, short, description, *args, **kwargs):
        self._msg(short, description, *args, **kwargs)

    def error(self, short, description):
        self.step._error = True
        self._msg(short, description)



class UpdateSchemaStep(BaseWizardStep):
    gladefile = 'UpdateSchemaStep'

    def _update_schema(self):
        # This method will run in a separate thread.
        migration = StoqlibSchemaMigration()
        try:
            migration.update(plugins=False)
            migration.update_plugins()
        except:
            self._error = True

        self._finished_update = True

    def _update_status(self, text):
        all = self.progressbar.get_text() or u''
        self.progressbar.set_text(all + text)

    def _pulse_timeout(self):
        time.sleep(0.1)
        self.progressbar.pulse()

        if self._finished_update:
            self.progressbar.set_fraction(1.0)
            self.wizard.cancel_button.set_sensitive(True)
            if not self._error:
                self.wizard.refresh_next(True)
                self._update_status(_(u' Done.'))
            else:
                self._update_status(_(u' Fail.'))

            # Prove the original System Notifier so that dialogs work
            # nicely
            provide_utility(ISystemNotifier, self.default_sn, replace=True)

        return not self._finished_update

    #
    # WizardStep
    #

    def post_init(self):
        # Save the System Notifier for later restauration
        self.default_sn = get_utility(ISystemNotifier)

        # We use our own SystemNotifier to display the messages in the step
        # itself
        self._my_sn = _MySystemNotifier(self)
        provide_utility(ISystemNotifier, self._my_sn, replace=True)

        self.wizard.refresh_next(False)
        self.wizard.enable_finish()
        self.wizard.next_button.set_label(_(u'Run Stoq'))

        self.wizard.cancel_button.set_label(gtk.STOCK_QUIT)
        self.wizard.cancel_button.set_sensitive(False)

        gobject.idle_add(self._pulse_timeout)

        self._finished_update = False
        self._error = False

        self._update_status(_(u'Applying database patches...'))
        self._update_thread = threading.Thread(target=self._update_schema)
        self._update_thread.start()

    def has_next_step(self):
        return False


#
# Main wizard
#


class SchemaUpdateWizard(BaseWizard):
    title = _("Updating Stoq")
    size = (450, 300)

    def __init__(self):
        first_step = UpdateWelcomeStep(None, wizard=self)
        BaseWizard.__init__(self, None, first_step, title=self.title)
        # Disable back until #2771 is solved
        self.previous_button.hide()

    #
    # WizardStep hooks
    #

    def finish(self):
        self.retval = True
        self.close()
