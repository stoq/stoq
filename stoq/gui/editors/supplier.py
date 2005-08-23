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
## Author(s):   Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
"""
stoq/gui/editors/supplier.py
    
    Supplier editor implementation.
"""


from stoqlib.gui.editors import BaseEditor

from stoq.gui.slaves.supplier import SupplierDetailsSlave
from stoq.gui.templates.person import CompanyEditorTemplate
from stoq.domain.interfaces import IIndividual, ISupplier, ICompany
from stoq.domain.person import Person, PersonAdaptToSupplier


class SupplierEditor(BaseEditor):
    title = _('Supplier Editor')
    gladefile = 'BaseTemplate'
    widgets = ('main_holder', )
    model_type = PersonAdaptToSupplier
    
    def create_model(self, conn):
        # XXX: This is a hack, we don't can create a client without a
        # person and an Individual/Company. This problem will be
        # resolved when the bug #2043 is fixed.
        person = Person(name="", connection=conn)
        company = person.addFacet(ICompany, connection=conn)
        return person.addFacet(ISupplier, connection=conn)

    def setup_slaves(self):
        company_facet = ICompany(self.model.get_adapted(),
                                 connection=self.conn)
        self.company_slave = CompanyEditorTemplate(self.conn, company_facet)
        self.attach_slave('main_holder', self.company_slave)

        self.details_slave = SupplierDetailsSlave(self.conn, self.model)
        self.company_slave.person_slave.attach_slave('person_status_holder',
                                                     self.details_slave)

    def on_confirm(self):
        self.company_slave.on_confirm()
        return self.model



