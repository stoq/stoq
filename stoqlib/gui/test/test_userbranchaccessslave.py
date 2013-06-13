# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

import mock

from stoqlib.gui.editors.personeditor import UserEditor
from stoqlib.gui.slaves.userbranchaccessslave import UserBranchAccessSlave
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestUserBranchAccessSlave(GUITest):
    def test_create(self):
        user = self.create_user()
        slave = UserBranchAccessSlave(self.store, user)
        self.check_slave(slave, 'user-branch-access-slave-create')

    @mock.patch('stoqlib.gui.slaves.userbranchaccessslave.info')
    @mock.patch('stoqlib.gui.slaves.userbranchaccessslave.warning')
    def test_confirm(self, warning, info):
        user = self.create_user()
        branch = self.create_branch()
        branch.person.company.fancy_name = u'branch'

        editor = UserEditor(self.store, user)
        editor._person_slave.address_slave.street.update('street')
        editor._person_slave.address_slave.streetnumber.update(15)
        editor._person_slave.address_slave.district.update('district')

        self.click(editor.main_dialog.ok_button)
        warning.assert_called_once_with(_(u'User must be associated to at '
                                          'least one branch.'))

        slave = editor.user_branches
        slave.target_combo.select_item_by_data(branch)
        slave.add()

        slave.add()
        info.assert_called_once_with('individual is already associated with '
                                     'branch.')

        self.click(editor.main_dialog.ok_button)
        associated_branches = list(user.get_associated_branches())
        self.check_editor(editor, 'user-branch-access-slave-confirm-editor',
                          [editor.retval, branch] + associated_branches)
