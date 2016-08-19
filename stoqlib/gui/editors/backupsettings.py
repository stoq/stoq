# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2016 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import gtk
from kiwi.datatypes import ValidationError
from kiwi.python import Settable

from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext as _


class BackupSettingsEditor(BaseEditor):
    model_name = _('Backup Configuration')
    model_type = Settable
    gladefile = 'BackupConfigurationEditor'
    proxy_widgets = ['key']
    confirm_widgets = proxy_widgets

    #
    #  BaseEditor
    #

    def validate_confirm(self):
        if self._old_key and self._old_key != self.model.key:
            msg = _("Changing the backup key will make any backup done with "
                    "the previous key unrecoverable. Are you sure?")
            if not yesno(msg, gtk.RESPONSE_NO, _("Change"), _("Keep old key")):
                return False

        return True

    def setup_proxies(self):
        self._old_key = self.model.key
        self.add_proxy(self.model, self.proxy_widgets)

    #
    #  Callbacks
    #

    def on_key__validate(self, widget, key):
        if len(key) < 10:
            return ValidationError(
                _("The backup key needs to have at least 10 characters"))
