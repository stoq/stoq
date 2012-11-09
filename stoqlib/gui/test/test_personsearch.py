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

from stoqlib.domain.transfer import TransferOrder, TransferOrderItem
from stoqlib.domain.person import (Client, Employee, EmployeeRoleHistory,
                                   Supplier, Transporter, EmployeeRole)
from stoqlib.domain.product import ProductSupplierInfo
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.domain.receiving import ReceivingOrderItem, ReceivingOrder
from stoqlib.gui.search.personsearch import (ClientSearch, EmployeeSearch,
                                             SupplierSearch, TransporterSearch,
                                             EmployeeRoleSearch, BranchSearch,
                                             UserSearch)
from stoqlib.domain.sale import Sale, SaleItem
from stoqlib.domain.commission import Commission
from stoqlib.gui.uitestutils import GUITest


class TestPersonSearch(GUITest):
    def testEmployeeSearch(self):
        self.clean_domain([TransferOrderItem, TransferOrder,
                           EmployeeRoleHistory, Employee])

        self.create_employee('Linus Torvalds')
        self.create_employee('John \'maddog\' Hall')

        search = EmployeeSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'employee-no-filter')

        search.set_searchbar_search_string('maddog')
        search.search.refresh()
        self.check_search(search, 'employee-string-filter')

    def testSupplierSearch(self):
        self.clean_domain([ReceivingOrderItem, ReceivingOrder, PurchaseItem,
                           PurchaseOrder, ProductSupplierInfo, Supplier])

        self.create_supplier('Eric S. Raymond', 'River Roupas')
        self.create_supplier('Guido van Rossum', 'Las Vegas Moda')

        search = SupplierSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'supplier-no-filter')

        search.set_searchbar_search_string('eri')
        search.search.refresh()
        self.check_search(search, 'supplier-string-filter')

    def testClientSearch(self):
        self.clean_domain([Commission, SaleItem, Sale, Client])

        self.create_client('Richard Stallman')
        self.create_client('Junio C. Hamano')

        search = ClientSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'client-no-filter')

        search.set_searchbar_search_string('ham')
        search.search.refresh()
        self.check_search(search, 'client-string-filter')

    def testTransporterSearch(self):
        self.clean_domain([ReceivingOrderItem, ReceivingOrder, PurchaseItem,
                           PurchaseOrder, Transporter])

        self.create_transporter('Peter Pan')
        self.create_transporter('Captain Hook')

        search = TransporterSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'transporter-no-filter')

        search.set_searchbar_search_string('pan')
        search.search.refresh()
        self.check_search(search, 'transporter-string-filter')

    def testEmployeeRoleSearch(self):
        self.clean_domain([TransferOrderItem, TransferOrder,
                           EmployeeRoleHistory, Employee, EmployeeRole])

        self.create_employee_role('Manager')
        self.create_employee_role('Salesperson')

        search = EmployeeRoleSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'employee-role-no-filter')

        search.set_searchbar_search_string('per')
        search.search.refresh()
        self.check_search(search, 'employee-role-string-filter')

    def testBranchSearch(self):
        self.create_branch(name='Las Vegas')
        self.create_branch(name='Dante')

        search = BranchSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'branch-no-filter')

        search.set_searchbar_search_string('dan')
        search.search.refresh()
        self.check_search(search, 'branch-string-filter')

    def testUserSearch(self):
        self.create_user(username='Homer')
        self.create_user(username='Bart')

        search = UserSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'user-no-filter')

        search.set_searchbar_search_string('hom')
        search.search.refresh()
        self.check_search(search, 'user-string-filter')
