# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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

""" Search dialog/Editor for publishers """

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.search.personsearch import BasePersonSearch
from stoqlib.gui.search.searchcolumns import SearchColumn

from optical.opticaldomain import OpticalMedicView
from optical.opticalslave import MedicEditor

_ = stoqlib_gettext


class OpticalMedicSearch(BasePersonSearch):
    title = _('Medic Search')
    editor_class = MedicEditor
    search_spec = OpticalMedicView
    size = (750, 450)
    search_lbl_text = _('Medic matching:')
    result_strings = _('medic'), _('medics')

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['name', 'phone_number', 'crm_number'])

    def get_columns(self):
        return [SearchColumn('name', title=_('Medic Name'), sorted=True,
                             data_type=str, searchable=True, expand=True),
                SearchColumn('phone_number', title=_('Phone Number'),
                             width=150, data_type=str),
                SearchColumn('crm_number', title=_('UPID'), width=150,
                             data_type=str)]

    def get_editor_model(self, model):
        return model.medic
