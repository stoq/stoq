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


from kiwi.currency import currency
from stoqlib.gui.editors.costcentereditor import CostCenterEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestCostCenterEditor(GUITest):
    def test_show(self):
        model = self.create_cost_center()
        model.budget = currency('10000')
        editor = CostCenterEditor(self.store, model)
        self.check_editor(editor, 'editor-cost-center-show')

    def test_create(self):
        editor = CostCenterEditor(self.store)
        self.check_editor(editor, 'editor-cost-center-create')
