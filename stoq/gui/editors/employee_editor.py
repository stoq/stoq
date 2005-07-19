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
gui/editors/employee_editor.py

    Base classes for employee editor
"""

import gtk
from stoqlib.gui.editors import BaseEditorSlave

from stoq.gui.editors.individual_editor import IndividualEditor
from stoq.domain.person import (WorkPermitData, MilitaryData, VoterData, 
                                EmployeePosition, Person, 
                                PersonAdaptToEmployee,
                                PersonAdaptToIndividual)
from stoq.domain.interfaces import IIndividual, IEmployee
from stoq.domain.account import BankAccount
from stoq.lib.parameters import get_system_parameter


class EmployeeDetailSlave(BaseEditorSlave):
    gladefile = 'EmployeeDetailsSlave'
    model_type = PersonAdaptToEmployee

    left_widgets_group = ('admission_date_lbl',
                          'position_lbl',
                          'registry_number_lbl',
                          'voter_id_number_lbl',
                          'voter_id_zone_lbl',
                          'voter_id_section_lbl',
                          'military_cert_category_lbl',
                          'military_cert_serie_lbl',
                          'military_cert_number_lbl',
                          'expire_vacation_lbl',
                          'salary_lbl')
    
    right_widgets_group = ('person_dependent_number_lbl',
                           'education_level_lbl',
                           'workpermit_number_lbl',
                           'workpermit_serie_lbl',
                           'pis_number_lbl',
                           'pis_registry_date_lbl',
                           'pis_bank_lbl',
                           'bank_lbl',
                           'bank_agency_lbl',
                           'bank_account_lbl')
    
    proxy_widgets = ('admission_date',
                     'registry_number',
                     'expire_vacation',
                     'salary',
                     'dependent_person_number',
                     'education_level')

    employee_position_widgets = ('position_name',)

    bank_account_widgets = ('name',
                            'agency',
                            'account')
    
    work_permit_widgets = ('workpermit_number',
                           'workpermit_serie',
                           'pis_number',
                           'pis_registry_date',
                           'pis_bank')
    
    military_widgets = ('military_doc_category',
                        'military_doc_serie',
                        'military_doc_number')

    voter_widgets = ('voter_id_number',
                     'voter_id_zone',
                     'voter_id_section')
    
    widgets = (right_widgets_group + left_widgets_group + proxy_widgets +
               employee_position_widgets + bank_account_widgets + 
               work_permit_widgets + military_widgets + voter_widgets)
    
    def __init__(self, parent):
        BaseEditorSlave.__init__(self, parent.conn, parent.role)
        self.setup_widgets()

    def setup_proxies(self):
        self.setup_combos()

        self.proxy = self.add_proxy(self.model, self.proxy_widgets)
        self.add_proxy(self.model.position, self.employee_position_widgets)
        
        if not self.model.workpermit_data:
            table = WorkPermitData
            self.model.workpermit_data = table(connection=self.conn)
        self.add_proxy(self.model.workpermit_data, self.work_permit_widgets)

        if not self.model.military_data:
            table = MilitaryData
            self.model.military_data = table(connection=self.conn)
        self.add_proxy(self.model.military_data, self.military_widgets)

        if not self.model.voter_data:
            self.model.voter_data = VoterData(connection=self.conn)
        self.add_proxy(self.model.voter_data, self.voter_widgets)

        if not self.model.bank_account:
            table = BankAccount
            self.model.bank_account = table(connection=self.conn)
        self.add_proxy(self.model.bank_account, self.bank_account_widgets)

    def setup_combos(self):
        positions = EmployeePosition.select(connection=self.conn)
        items = [(p.name, p) for p in positions]
        self.position_name.prefill(items)

    def setup_widgets(self):
        self.right_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self.left_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        
        for widget in self.right_widgets_group:
            w = getattr(self, widget)
            self.right_size_group.add_widget(w)
        
        for widget in self.left_widgets_group:
            w = getattr(self, widget)
            self.left_size_group.add_widget(w)


class EmployeeStatusSlave(BaseEditorSlave):
    gladefile = 'EmployeeStatusSlave'
    model_type = PersonAdaptToEmployee
    widgets = ('normal', 'away', 'vacation', 'off')
    
    def __init__(self, parent):
        BaseEditorSlave.__init__(self, parent.conn, parent.role)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.widgets)


class EmployeeEditor(IndividualEditor):
    title = _("Employee Editor")
    model_type = PersonAdaptToIndividual
    
    def __init__(self, conn, role=None):
        if not role:
            person_obj = Person(connection=conn, name='')
            individual = person_obj.addFacet(IIndividual, connection=conn)
            param = get_system_parameter(conn)
            position = param.DEFAULT_EMPLOYEE_POSITION
            role = person_obj.addFacet(IEmployee, position=position, 
                                       connection=conn)
        else:
            individual = IIndividual(role.get_adapted(), connection=conn)
        self.role = role
        IndividualEditor.__init__(self, conn, individual)

    def setup_slaves(self):
        IndividualEditor.setup_slaves(self)
        # Employee Status
        self.status_slave = EmployeeStatusSlave(self)
        self.attach_slave('person_status_holder', self.status_slave)
        # Employee Details
        self.custom_holder.show()
        label = _('Employee Data')
        self.notebook1.set_tab_label_text(self.custom_holder, label)
        self.details_slave = EmployeeDetailSlave(self)
        self.attach_slave('custom_holder', self.details_slave)

    def on_confirm(self):
        IndividualEditor.on_confirm(self)
        return self.role
