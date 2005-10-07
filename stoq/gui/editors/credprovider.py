# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Author(s):   Ariqueli Tejada Fonseca     <aritf@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/editors/credprovider.py
    
    Credit Provider editor implementation.
"""


from datetime import datetime
import gettext

from stoqlib.gui.editors import BaseEditor

from stoq.gui.slaves.credprovider import CreditProviderDetailsSlave
from stoq.gui.templates.person import CompanyEditorTemplate
from stoq.domain.interfaces import ICompany, ICreditProvider
from stoq.domain.person import Person, PersonAdaptToCreditProvider

_ = gettext.gettext

class CreditProviderEditor(BaseEditor):

    model_name = _('Credit Provider')
    model_type = PersonAdaptToCreditProvider
    gladefile = 'BaseTemplate'
    widgets = ('main_holder', )



    #
    # BaseEditor hooks
    #
    


    def create_model(self, conn):
        # XXX: It will be much better creating a client without a
        # person and an Individual/Company. Waiting for bug 2043
        person = Person(name="", connection=conn)
        company = person.addFacet(ICompany, connection=conn)
        return person.addFacet(ICreditProvider, short_name='',
                               open_contract_date=datetime.today(),  
                               connection=conn)

    def get_title_model_attribute(self, model):
        return model.get_adapted().name

    def setup_slaves(self):
        company_facet = ICompany(self.model.get_adapted(),
                                 connection=self.conn)
        self.company_slave = CompanyEditorTemplate(self.conn, company_facet)
        self.attach_slave('main_holder', self.company_slave)

        self.details_slave = CreditProviderDetailsSlave(self.conn, self.model)
        self.company_slave.person_slave.attach_slave('person_status_holder',
                                                     self.details_slave)

    def on_confirm(self):
        self.company_slave.on_confirm()
        return self.model


