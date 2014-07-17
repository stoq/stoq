# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.workorder import WorkOrder, WorkOrderHistory
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.templates.persontemplate import BasePersonRoleEditor
from stoqlib.lib.translation import stoqlib_gettext

from .opticaldomain import OpticalMedic

_ = stoqlib_gettext


class MedicEditor(BasePersonRoleEditor):
    model_name = _(u'Medic')
    title = _(u'New Medic')
    model_type = OpticalMedic
    gladefile = 'BaseTemplate'

    def create_model(self, store):
        # Document used in MedicEditor is the CRM number
        crm = self.document
        self.document = None

        person = BasePersonRoleEditor.create_model(self, store)
        medic = store.find(OpticalMedic, person=person).one()
        if medic is None:
            medic = OpticalMedic(person=person, store=store, crm_number=crm)
        return medic

    def setup_slaves(self):
        from .opticalslave import MedicDetailsSlave
        BasePersonRoleEditor.setup_slaves(self)

        tab_text = _('Medic Details')
        self.medic_details_slave = MedicDetailsSlave(self.store, self.model,
                                                     visual_mode=self.visual_mode)
        self.main_slave._person_slave.add_extra_tab(tab_text,
                                                    self.medic_details_slave)


class OpticalWorkOrderEditor(BaseEditor):
    """A simple editor to use :class:`.WorkOrderOpticalSlave` alone"""

    title = _(u'Optical Details')
    model_type = WorkOrder
    gladefile = 'HolderTemplate'

    #
    #  BaseEditor
    #

    def setup_slaves(self):
        from .opticalslave import WorkOrderOpticalSlave
        self.slave = WorkOrderOpticalSlave(self.store, self.model,
                                           show_finish_date=False,
                                           visual_mode=self.visual_mode)
        self.attach_slave('place_holder', self.slave)

        self._proxy_widgets = [(name, getattr(self.slave, name)) for
                               name in self.slave.proxy_widgets]
        self._old_values = {name: widget.read() for
                            name, widget in self._proxy_widgets}

    def on_confirm(self):
        new_values = {name: widget.read() for
                      name, widget in self._proxy_widgets}
        if self._old_values == new_values:
            return

        WorkOrderHistory.add_entry(
            self.store, self.model, what=_(u"Optical details"),
            notes=_(u"Optical details updated..."))
