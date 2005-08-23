# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
stoq/gui/slaves/company.py

    Company editor slaves implementation.
"""


from stoqlib.gui.editors import BaseEditorSlave

from stoq.domain.person import PersonAdaptToCompany


class CompanyDocumentsSlave(BaseEditorSlave):
    model_type = PersonAdaptToCompany
    gladefile = 'CompanyDocumentsSlave'
    widgets = ('cnpj', 
               'fancy_name',
               'state_registry')

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.widgets)

