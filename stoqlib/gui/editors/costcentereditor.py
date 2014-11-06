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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
"""An editor for |costcenter| objects"""

import collections

from kiwi.ui.forms import BoolField, MultiLineField, PriceField, TextField

from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.costcenter import CostCenter

_ = stoqlib_gettext


class CostCenterEditor(BaseEditor):
    model_name = _('Cost Center')
    size = (300, -1)
    model_type = CostCenter

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            name=TextField(_('Name'), mandatory=True, proxy=True),
            budget=PriceField(_('Budget'), mandatory=True, proxy=True),
            description=MultiLineField(_('Description'), mandatory=True, proxy=True),
            is_active=BoolField(_('Active'), proxy=True),
        )

    #
    # BaseEditor Hooks
    #

    def create_model(self, store):
        return CostCenter(store=store)
