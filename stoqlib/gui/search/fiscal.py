# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
##  Author(s): Evandro Vale Miquelito   <evandro@async.com.br>
##
##
""" Search dialogs for fiscal objects """

from kiwi.ui.widgets.list import Column

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.editors.fiscal import CfopEditor
from stoqlib.domain.fiscal import CfopData


_ = stoqlib_gettext


class CfopSearch(SearchEditor):
    title = _("CFOP Search")
    table = CfopData
    editor_class = CfopEditor
    size = (465, 390)
    searchbar_result_strings = _("CFOP"), _("CFOPs")

    #
    # SearchDialog Hooks
    #

    def get_columns(self):
        return [Column('code', _('CFOP'), data_type=str, sorted=True,
                       width=90),
                Column('description', _('Description'), data_type=str,
                       searchable=True, expand=True)]
