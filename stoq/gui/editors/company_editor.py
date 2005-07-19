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
gui/editors/company_editor.py

    Base classes to company editors
"""

from stoqlib.gui.editors import BaseEditorSlave

from stoq.gui.editors.person_editor import PersonEditor
from stoq.domain.person import (Person, PersonAdaptToCompany,
                                PersonAdaptToSupplier)
from stoq.domain.interfaces import ICompany, ISupplier
   

class SupplierDetailsSlave(BaseEditorSlave):
    gladefile = 'SupplierDetailsSlave'
    model_type = PersonAdaptToSupplier
    widgets = ('active', 'inactive', 'blocked', 'product_desc')
    
    def __init__(self, parent):
        BaseEditorSlave.__init__(self, parent.conn, parent.role)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.widgets)


class CompanyDocumentsSlave(BaseEditorSlave):
    gladefile = 'CompanyDocumentsSlave'
    model_type = PersonAdaptToCompany
    widgets = ('cnpj', 'fancy_name', 'state_registry')
    
    def __init__(self, parent):
        BaseEditorSlave.__init__(self, parent.conn, parent.model)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.widgets)


class CompanyEditor(PersonEditor):
    title = _('Company Editor')
    model_type = PersonAdaptToCompany

    def __init__(self, conn, model=None):
        if not model:
            model = Person(connection=conn, name='')
            company = model.addFacet(ICompany, connection=conn)
        else:
            company = model
        PersonEditor.__init__(self, conn, company)

    def setup_slaves(self):
        PersonEditor.setup_slaves(self)
        # Company Documents
        company_docs = CompanyDocumentsSlave(self)
        self.attach_slave('person_id_holder', company_docs)


class SupplierEditor(CompanyEditor):
    title = _('Supplier Editor')
    model_type = PersonAdaptToCompany
    
    def __init__(self, conn, supplier=None):
        if not supplier:
            person_obj = Person(connection=conn, name='')
            company = person_obj.addFacet(ICompany, connection=conn, cnpj='')
            supplier = person_obj.addFacet(ISupplier, connection=conn)
        else:
            adapted = supplier.get_adapted()
            company = ICompany(adapted, connection=conn)
        self.role = supplier
        CompanyEditor.__init__(self, conn, company)

    def setup_slaves(self):
        CompanyEditor.setup_slaves(self)
        # Supplier Details
        supplier_details = SupplierDetailsSlave(self)
        self.attach_slave('person_status_holder', supplier_details)

    def on_confirm(self):
        CompanyEditor.on_confirm(self)
        return self.role
    



