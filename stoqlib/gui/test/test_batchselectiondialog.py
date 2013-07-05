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

import datetime

from stoqlib.api import api
from stoqlib.gui.dialogs.batchselectiondialog import BatchSelectionDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestBatchSelectionDialog(GUITest):
    def test_create(self):
        storable = self.create_storable(is_batch=True)
        batch = self.create_storable_batch(storable=storable,
                                           batch_number=u'1')
        batch.create_date = datetime.date(2010, 10, 10)
        batch = self.create_storable_batch(storable=storable,
                                           batch_number=u'2')
        batch.create_date = datetime.date(2011, 11, 11)
        batch = self.create_storable_batch(storable=storable,
                                           batch_number=u'3')
        batch.create_date = datetime.date(2012, 12, 12)

        storable.register_initial_stock(10, api.get_current_branch(self.store),
                                        1, u'1')
        storable.register_initial_stock(15, api.get_current_branch(self.store),
                                        1, u'2')
        storable.register_initial_stock(8, api.get_current_branch(self.store),
                                        1, u'3')

        dialog = BatchSelectionDialog(self.store, storable, 33)
        for entry in dialog._spins.keys():
            entry.update(1)
            dialog._spins[entry].update(12)

        for entry in dialog._spins.keys()[1:]:
            entry.update(2)
            dialog._spins[entry].update(7)

        for entry in dialog._spins.keys()[2:]:
            entry.update(3)
            dialog._spins[entry].update(8)

        dialog.existing_batches_expander.set_expanded(True)

        self.check_dialog(dialog, 'dialog-batch-selection-dialog-create')
