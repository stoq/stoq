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
gui/editors/client_editor.py

    Base classes to client editors
"""

from stoqlib.gui import editors

from stoq.gui.editors.individual_editor import IndividualEditor
from stoq.domain.person import (Person, PersonAdaptToClient,
                                PersonAdaptToIndividual)
from stoq.domain.interfaces import IIndividual, IClient


class ClientStatusSlave(editors.BaseEditorSlave):
    gladefile = 'ClientStatusSlave'
    model_type = PersonAdaptToClient
    
    widgets = ('ok', 'indebted', 'insolvent', 'inactive')
    
    def __init__(self, parent):
        editors.BaseEditorSlave.__init__(self, parent.conn, parent.role)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.widgets)


class ClientEditor(IndividualEditor):
    title = _("Client Editor")
    model_type = PersonAdaptToIndividual
    
    def __init__(self, conn, role=None):
        if not role:
            person_obj = Person(name='', connection=conn)
            individual = person_obj.addFacet(IIndividual, connection=conn)
            role = person_obj.addFacet(IClient, connection=conn)
        else:
            individual = IIndividual(role.get_adapted(), connection=conn)
        self.role = role
        IndividualEditor.__init__(self, conn, individual)

    def setup_slaves(self):
        IndividualEditor.setup_slaves(self)
        # Client Status
        status_slave = ClientStatusSlave(self) 
        self.attach_slave('person_status_holder', status_slave)

    def on_confirm(self):
        IndividualEditor.on_confirm(self)
        return self.role
