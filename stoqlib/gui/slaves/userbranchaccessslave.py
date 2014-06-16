# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.person import (Branch, UserBranchAccess)
from stoqlib.gui.editors.baseeditor import BaseRelationshipEditorSlave
from stoqlib.lib.message import info, warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class UserBranchAccessSlave(BaseRelationshipEditorSlave):
    model_type = UserBranchAccess
    target_name = _('Branch')

    def __init__(self, store, user):
        self._user = user
        self._store = store
        BaseRelationshipEditorSlave.__init__(self, self._store)

        self.relations_list.edit_button.hide()

    #
    # Slave hooks
    #

    def create_model(self):
        user = self._user
        branch = self.target_combo.get_selected_data()

        if UserBranchAccess.has_access(self._store, user, branch):
            info(_(u'%s is already associated with %s.') %
                 (user.person.name, branch.get_description()))
            return

        return UserBranchAccess(store=self._store,
                                user=user,
                                branch=branch)

    def get_columns(self):
        return [Column('branch.description', title=_('Branch Name'),
                       data_type=str, expand=True), ]

    def get_targets(self):
        branches = Branch.get_active_branches(self._store)
        return api.for_person_combo(branches)

    def get_relations(self):
        return self._user.get_associated_branches()

    def validate_confirm(self):
        if self._user.get_associated_branches().count() <= 0:
            warning(_(u'User must be associated to at least one branch.'))
            return False

        return True
