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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" General slaves for branch management"""

from stoqlib.api import api
from stoqlib.domain.person import Branch, Employee
from stoqlib.gui.editors.baseeditor import BaseEditorSlave


class BranchDetailsSlave(BaseEditorSlave):
    gladefile = 'BranchDetailsSlave'
    model_type = Branch
    proxy_widgets = ('active_check',
                     'manager',
                     'crt')

    crt_options = (
        ('1 - Simples Nacional', 1),
        ('2 - Simples Nacional – excesso de sublimite da receita bruta', 2),
        ('3 - Regime Normal', 3),
    )

    def _setup_manager_entry(self):
        employees = Employee.get_active_employees(self.conn)
        self.manager.prefill(api.for_combo(employees))

    def _setup_crt_combo(self):
        self.crt.prefill(self.crt_options)

    def setup_proxies(self):
        self._setup_manager_entry()
        self._setup_crt_combo()
        self.proxy = self.add_proxy(self.model,
                                    BranchDetailsSlave.proxy_widgets)
