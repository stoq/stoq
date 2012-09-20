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

from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.translation import stoqlib_gettext as _


class TestProductSearch(GUITest):

    def _show_search(self):
        search = ProductSearch(self.trans)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def testShow(self):
        search = self._show_search()
        self.check_search(search, 'search-product-show')

    @mock.patch('stoqlib.gui.base.search.run_dialog')
    def testShowWithPermission(self, run_dialog):
        search = self._show_search()

        self.assertVisible(search._toolbar, ['new_button'])
        self.assertSensitive(search._toolbar, ['edit_button'])
        self.assertEquals(search._toolbar.edit_button_label.get_label(),
                          _('_Edit...'))
        self.click(search._toolbar.edit_button)

        # We have permission to edit Product, so visual_mode should be false
        args, kwargs = run_dialog.call_args
        self.assertTrue('visual_mode' in kwargs)
        self.assertEquals(kwargs['visual_mode'], False)

    @mock.patch('stoqlib.gui.base.search.run_dialog')
    def testShowWithoutPermission(self, run_dialog):
        # Our only permission now is to see details
        pm = PermissionManager.get_permission_manager()
        pm.set('Product', pm.PERM_ONLY_DETAILS)
        search = self._show_search()

        # New button shoud not be visible and edit button should actually be
        # 'Details'
        self.assertNotVisible(search._toolbar, ['new_button'])
        self.assertSensitive(search._toolbar, ['edit_button'])
        self.assertEquals(search._toolbar.edit_button_label.get_label(),
                          _('Details'))

        # Editor should be called with visual mode set.
        self.click(search._toolbar.edit_button)
        args, kwargs = run_dialog.call_args
        self.assertTrue('visual_mode' in kwargs)
        self.assertEquals(kwargs['visual_mode'], True)
