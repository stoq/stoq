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
/stoq/gui/slaves/employee.py

    Employee editor slaves implementation.
"""


import gtk
from stoqlib.gui.editors import BaseEditorSlave

from stoq.lib.runtime import new_transaction
from stoq.domain.person import (WorkPermitData, MilitaryData, VoterData,
                                EmployeePosition, PersonAdaptToEmployee)
from stoq.domain.account import BankAccount


class EmployeeDetailsSlave(BaseEditorSlave):
    model_type = PersonAdaptToEmployee
    gladefile = 'EmployeeDetailsSlave'

    # 
    # Widgets specification for size groups.
    #

    left_widgets_group =  ('admission_date_label',
                           'registry_number_label',
                           'position_label',
                           'military_cert_serie_label',
                           'military_cert_category_label',
                           'military_cert_number_label',
                           'voter_id_number_label',
                           'voter_id_zone_label',
                           'voter_id_section_label',
                           'expire_vacation_label',
                           'salary_label')

    right_widgets_group = ('person_dependent_number_label',
                           'education_level_label',
                           'pis_number_label',
                           'pis_registry_date_label',
                           'pis_bank_label',
                           'workpermit_number_label',
                           'workpermit_serie_label',
                           'bank_account_label',
                           'bank_label',
                           'bank_agency_label')

    #
    # Proxy widgets
    #

    employee_widgets =    ('admission_date',
                           'registry_number',
                           'expire_vacation',
                           'salary',
                           'dependent_person_number',
                           'education_level',
                           'position')

    bank_account_widgets = ('name',
                            'account',
                            'agency')

    work_permit_widgets = ('workpermit_number',
                           'workpermit_serie',
                           'pis_number',
                           'pis_registry_date',
                           'pis_bank')

    voter_widgets =       ('voter_id_number',
                           'voter_id_zone',
                           'voter_id_section')

    military_widgets =    ('military_doc_category',
                           'military_doc_serie',
                           'military_doc_number')

    widgets = (right_widgets_group + left_widgets_group + employee_widgets + 
               bank_account_widgets + work_permit_widgets + voter_widgets + 
               military_widgets)

    def setup_widgets(self):
        self.right_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self.left_size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        for widget in self.left_widgets_group:
            w = getattr(self, widget)
            self.left_size_group.add_widget(w)

        for widget in self.right_widgets_group:
            w = getattr(self, widget)
            self.right_size_group.add_widget(w)

        self.salary.set_data_format('%.2f')

    def setup_combos(self):
        positions = EmployeePosition.select(connection=self.conn)
        items = [(p.name, p) for p in positions]

        self.position.prefill(items)

    #
    # BaseEditorSlave hooks
    # 

    def setup_proxies(self):
        self.setup_widgets()
        self.setup_combos()

        assert(self.model)

        proxy_info = [
            ('workpermit_data', self.work_permit_widgets, WorkPermitData),
            ('military_data', self.military_widgets, MilitaryData),
            ('voter_data', self.voter_widgets, VoterData),
            ('bank_account', self.bank_account_widgets, BankAccount)
        ]
        self.proxy = self.add_proxy(self.model, self.employee_widgets)

        for name, widgets, table in proxy_info:
            obj = getattr(self.model, name)
            if not obj and table:
                obj = table(connection=self.conn)
            setattr(self.model, name, obj)
            self.add_proxy(obj, widgets)


class EmployeeStatusSlave(BaseEditorSlave):
    gladefile = 'EmployeeStatusSlave'
    widgets = ('normal', 'away', 'vacation', 'off')
    model_type = PersonAdaptToEmployee

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.widgets)

    
