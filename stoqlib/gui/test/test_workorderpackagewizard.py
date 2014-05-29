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

import mock

from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.workorderpackagewizard import WorkOrderPackageReceiveWizard


class TestSaleReturnWizard(GUITest):
    @mock.patch('stoqlib.domain.workorder.get_current_branch')
    @mock.patch('stoqlib.gui.wizards.workorderpackagewizard.get_current_branch')
    def test_create(self, gcb1, gcb2):
        source_branch = self.create_branch()
        destination_branch = self.create_branch()
        gcb1.return_value = source_branch
        gcb2.return_value = source_branch

        package = self.create_workorder_package(source_branch=source_branch)
        package.destination_branch = destination_branch

        for i in xrange(10):
            wo = self.create_workorder(description=u"Equipment %d" % i)
            wo.current_branch = source_branch
            wo.client = self.create_client()
            wo.identifier = 666 + i
            wo.open_date = datetime.datetime(2013, 1, 1)
            package.add_order(wo)

        package.send()
        package.send_date = datetime.datetime(2013, 1, 2)
        # Now set current_branch as destination_branch so we are able to
        # receive the package on the wizard
        gcb1.return_value = destination_branch
        gcb2.return_value = destination_branch

        wizard = WorkOrderPackageReceiveWizard(self.store)
        step = wizard.get_current_step()

        self.check_wizard(wizard, 'wizard-workorderpackagereceive-selection-step')

        with mock.patch('stoqlib.gui.wizards.workorderpackagewizard.warning') as w:
            self.click(wizard.next_button)
            w.assert_called_once_with(
                "You need to select a package to receive first.")

        step.packages.select(step.packages[0])
        self.click(wizard.next_button)
        step = wizard.get_current_step()
        self.check_wizard(wizard, 'wizard-workorderpackagereceive-orders-step')

        self.click(wizard.next_button)
        with mock.patch.object(wizard.model, 'receive') as receive:
            self.click(wizard.next_button)
            self.assertEqual(receive.call_count, 1)
