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
"""Dialog for listing payment categories"""

import collections

from kiwi.datatypes import ValidationError
from kiwi.ui.forms import ColorField, TextField

from stoqlib.domain.workorder import WorkOrderCategory
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.colorutils import get_random_color
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class WorkOrderCategoryEditor(BaseEditor):
    """An editor for |workordercategory| objects"""

    model_name = _('Work order category')
    model_type = WorkOrderCategory
    confirm_widgets = ['name']

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            name=TextField(_('Name'), proxy=True),
            color=ColorField(_('Color'), proxy=True),
        )

    #
    # BaseEditor
    #

    def create_model(self, store):
        used_colors = set([woc.color for woc in store.find(WorkOrderCategory)])
        color = get_random_color(ignore=used_colors)
        return WorkOrderCategory(
            store=store,
            name=u'',
            color=color)

    def setup_proxies(self):
        self.name.grab_focus()

    #
    # Kiwi Callbacks
    #

    def on_name__validate(self, widget, name):
        if not name:
            return ValidationError(
                _("The work order category should have a name."))
        if self.model.check_unique_value_exists(WorkOrderCategory.name, name):
            return ValidationError(
                _("The work order category '%s' already exists.") % name)
