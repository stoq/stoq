# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009-2012 Async Open Source <http://www.async.com.br>
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
##
""" Schema Update Wizard """

import platform
import sys

import glib
import gtk

from stoqlib.api import api
from stoqlib.gui.base.wizards import BaseWizard, BaseWizardStep
from stoqlib.gui.utils.logo import render_logo_pixbuf
from stoqlib.gui.widgets.processview import ProcessView
from stoqlib.lib.kiwilibrary import library
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext as _

import stoq

#
# Wizard Steps
#


class UpdateWelcomeStep(BaseWizardStep):
    gladefile = 'UpdateWelcomeStep'

    def post_init(self):
        self.title_label.set_size('xx-large')
        self.title_label.set_bold(True)
        self.logo.set_from_pixbuf(render_logo_pixbuf('update'))
        self.wizard.next_button.grab_focus()

    def next_step(self):
        return UpdateSchemaStep(None, self.wizard)


class UpdateSchemaStep(BaseWizardStep):
    gladefile = 'UpdateSchemaStep'

    #
    # WizardStep
    #

    def post_init(self):
        self._finished = False
        self.process_view = ProcessView()
        self.process_view.listen_stderr = True
        self.process_view.connect('read-line', self._on_processview__readline)
        self.process_view.connect('finished', self._on_processview__finished)
        self.expander.add(self.process_view)
        self._launch_stoqdbadmin()
        glib.timeout_add(50, self._on_timeout_add)

    def has_next_step(self):
        return False

    # Private

    def _parse_process_line(self, line):
        # Errors and other messages thrown by stoqdbadmin are not displayed in
        # this wizard. Using info here instead of error, so that the user can
        # still se the log.
        if line.startswith('ERROR:'):
            msg = line[7:]
            info(msg)

        LOG_CATEGORY = 'stoqlib.database.create'
        log_pos = line.find(LOG_CATEGORY)
        if log_pos == -1:
            return
        line = line[log_pos + len(LOG_CATEGORY) + 1:]
        longer = None
        if line.startswith('PATCH:'):
            patch = line.split(':', 1)[1]
            text = _("Applying patch %s ...") % (patch, )
        elif line.startswith('BACKUP-START:'):
            text = _("Creating a database backup")
            longer = _('Creating a database backup in case anything goes wrong.')
        elif line.startswith('RESTORE-START:'):
            text = _("Restoring database backup")
            longer = _(
                'Stoq update failed.\n\n'
                'We will try to restore the current database.\n\n'
                'This may take some time.')
        elif line.startswith('RESTORE-DONE:'):
            msg = line.split(':', 1)[1]
            text = _("Database backup restored")
            longer = _(
                'Stoq database update failed but the database was restored.\n'
                'An automatic crash report was submitted. Please, '
                'enter in contact at <b>stoq-users@stoq.com.br</b> for '
                'assistance in recovering your database and making it '
                'possible to use Stoq %s again.\n\n'
                'A backup database was created as <b>%s</b>') % (
                stoq.version, msg, )
        else:
            return
        self.progressbar.set_text(text)
        if not longer:
            longer = ''
        self.label.set_markup(longer)

    def _launch_stoqdbadmin(self):
        self.wizard.disable_next()
        if sys.argv[0].endswith('.egg'):
            args = [sys.executable, sys.argv[0]]
        elif platform.system() == 'Windows':
            if library.uninstalled:
                args = ['stoq.bat']
            else:
                args = ['stoq.exe']
        else:
            args = ['stoq']

        args.extend(['dbadmin', 'updateschema', '-v'])
        args.extend(api.db_settings.get_command_line_arguments())
        self.process_view.execute_command(args)
        self.progressbar.set_text(_('Applying database patches...'))

    def _finish(self, returncode):
        self._finished = True
        if returncode:
            self.wizard.cancel_button.set_label(gtk.STOCK_QUIT)
            self.progressbar.set_fraction(0.0)
        else:
            # Migration may have changed some parameters, so clear the cache.
            api.sysparam.clear_cache()
            self.wizard.cancel_button.set_sensitive(True)
            self.progressbar.set_text(_("Done. Click 'Forward' to continue"))
            self.progressbar.set_fraction(1.0)
            self.wizard.enable_next()
            self.wizard.next_button.grab_focus()

    # Callbacks

    def _on_processview__readline(self, view, line):
        self._parse_process_line(line)

    def _on_processview__finished(self, view, returncode):
        self._finish(returncode)

    def _on_timeout_add(self):
        if self._finished:
            return False
        self.progressbar.pulse()
        return True


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
