# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010-2012 Async Open Source <http://www.async.com.br>
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
"""Dialog for listing client categories"""

import collections

from kiwi.datatypes import ValidationError
from kiwi.ui.forms import PercentageField
from kiwi.ui.forms import TextField

from stoqlib.api import api
from stoqlib.domain.person import ClientCategory
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ClientCategoryEditor(BaseEditor):
    model_name = _('Client Category')
    model_type = ClientCategory
    confirm_widgets = ['name',
                       'max_discount']

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            name=TextField(_('Name'), proxy=True),
            max_discount=PercentageField(_('Max Discount'), proxy=True),
        )

    def create_model(self, store):
        return ClientCategory(name=u'', store=store)

    def setup_proxies(self):
        self.name.grab_focus()

    #
    # Kiwi Callbacks
    #

    def on_name__validate(self, widget, new_name):
        if not new_name:
            return ValidationError(
                _("The client category should have a name."))
        if self.model.check_unique_value_exists(ClientCategory.name,
                                                new_name):
            return ValidationError(
                _("The client category '%s' already exists.") % new_name)


if __name__ == '__main__':  # pragma nocover
    ec = api.prepare_test()
    model = ec.create_client_category()
    run_dialog(ClientCategoryEditor,
               parent=None, store=ec.store, model=model)
