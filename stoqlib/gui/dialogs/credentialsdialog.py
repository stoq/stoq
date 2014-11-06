# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

import collections

from kiwi.ui.forms import PasswordField, TextField
from kiwi.python import Settable

from stoqlib.api import api
from stoqlib.domain.person import LoginUser
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.exceptions import LoginError
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CredentialsDialog(BaseEditor):
    """This dialog is used to collect the credentials of a user. Returns None
    if not possible to authenticate the user, or the user if possible.
    """
    model_type = Settable
    title = _(u'Credentials Dialog')

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            username=TextField(_('Username'), mandatory=True, proxy=True),
            password=PasswordField(_('Password'), proxy=True),
        )

    confirm_widgets = ('password', )

    #
    # BaseEditor Hooks
    #

    def create_model(self, store):
        return Settable(username=u'', password=u'')

    #
    # Callbacks
    #

    def on_username__activate(self, widget):
        self.password.grab_focus()

    def on_confirm(self):
        password = LoginUser.hash(self.model.password)
        current_branch = api.get_current_branch(self.store)

        try:
            self.retval = LoginUser.authenticate(self.store,
                                                 self.model.username, password,
                                                 current_branch)
        except LoginError as e:
            self.retval = None
            warning(str(e))
