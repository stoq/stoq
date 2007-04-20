# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Bruno Rafael Garcia         <brg@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Main gui definition for admin application.  """

import gettext

from kiwi.enums import SearchFilterPosition
from kiwi.ui.widgets.list import Column
from kiwi.ui.search import ComboSearchFilter
from sqlobject.sqlbuilder import AND

from stoqlib.database.database import finish_transaction
from stoqlib.domain.person import Person, PersonAdaptToUser
from stoqlib.domain.profile import UserProfile
from stoqlib.gui.base.columns import ForeignKeyColumn
from stoqlib.gui.dialogs.devices import DeviceSettingsDialog
from stoqlib.gui.dialogs.paymentmethod import PaymentMethodsDialog
from stoqlib.gui.editors.personeditor import UserEditor
from stoqlib.gui.editors.sellableeditor import SellableTaxConstantsDialog
from stoqlib.gui.parameters import ParametersListingDialog
from stoqlib.gui.search.fiscalsearch import CfopSearch, FiscalBookEntrySearch
from stoqlib.gui.search.personsearch import (EmployeeRoleSearch,
                                             EmployeeSearch,
                                             BranchSearch)
from stoqlib.gui.search.profilesearch import UserProfileSearch
from stoqlib.gui.search.stationsearch import StationSearch
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.defaults import ALL_ITEMS_INDEX

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext


class AdminApp(SearchableAppWindow):

    app_name = _('Administrative')
    app_icon_name = 'stoq-admin-app'
    gladefile = "admin"
    search_table = PersonAdaptToUser
    search_label = _('matching:')

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._update_view()

    def create_filters(self):
        # FIXME: Convert the query to a Viewable so we can add name
        self.set_text_field_columns(['username'])
        status_filter = ComboSearchFilter(_('Show users with status'),
                                          self._get_status_values())
        self.executer.add_filter_query_callback(
            status_filter, self._get_status_query)
        self.add_filter(status_filter, position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [Column('username', title=_('Login Name'), sorted=True,
                       data_type=str, width=150, searchable=True),
                ForeignKeyColumn(UserProfile, 'name', title=_('Profile'),
                                 obj_field='profile', data_type=str,
                                 width=150, expand=True),
                ForeignKeyColumn(Person, 'name', title=_('Name'),
                                 data_type=str, adapted=True,
                                 width=300),
                Column('status_str', title=_('Status'), data_type=str)]

    #
    # Private
    #

    def _get_status_values(self):
        items = [(v, k) for k, v in PersonAdaptToUser.statuses.items()]
        items.insert(0, (_('Any'), ALL_ITEMS_INDEX))
        return items

    def _get_status_query(self, state):
        query = AND(PersonAdaptToUser.q._originalID == Person.q.id,
                    UserProfile.q.id == PersonAdaptToUser.q.profileID)
        if state.value == PersonAdaptToUser.STATUS_ACTIVE:
            query = AND(query, PersonAdaptToUser.q.is_active == True)
        elif state.value == PersonAdaptToUser.STATUS_INACTIVE:
            query = AND(query, PersonAdaptToUser.q.is_active == False)

        return query

    def _update_view(self):
        has_selected = self.results.get_selected() is not None
        self.edit_button.set_sensitive(has_selected)

    def _edit_user(self):
        user = self.results.get_selected()
        model =  run_person_role_dialog(UserEditor, self, self.conn, user)
        if finish_transaction(self.conn, model):
            self.results.update(model)

    def _add_user(self):
        model = run_person_role_dialog(UserEditor, self, self.conn)
        if finish_transaction(self.conn, model):
            self.refresh()
            model = self.table.get(model.id, connection=self.conn)
            self.results.select(model)

    #
    # Callbacks
    #

    def _on_fiscalbook_action_clicked(self, button):
        self.run_dialog(FiscalBookEntrySearch, self.conn, hide_footer=True)

    def _on_new_user_action_clicked(self, button):
        self._add_user()

    def on_results__double_click(self, results, user):
        self._edit_user()

    def on_results__selection_changed(self, results, user):
        self._update_view()

    def _on_cfop_action_clicked(self, button):
        self.run_dialog(CfopSearch, self.conn, hide_footer=True)

    def _on_employees_action_clicked(self, button):
        self.run_dialog(EmployeeSearch, self.conn, hide_footer=True)

    def _on_user_profiles_action_clicked(self, button):
        self.run_dialog(UserProfileSearch, self.conn)

    def _on_employee_role__action_clicked(self, button):
        self.run_dialog(EmployeeRoleSearch, self.conn)

    def _on_branch_action_clicked(self, button):
        self.run_dialog(BranchSearch, self.conn, hide_footer=True)

    def _on_branchstation_action_clicked(self, button):
        self.run_dialog(StationSearch, self.conn, hide_footer=True)

    def on_add_button__clicked(self, button):
        self._add_user()

    def on_edit_button__clicked(self, button):
        self._edit_user()

    def on_devices_setup_activate(self, button):
        self.run_dialog(DeviceSettingsDialog, self.conn)

    def on_system_parameters_activate(self, button):
        self.run_dialog(ParametersListingDialog, self.conn)

    def on_payment_methods_activate(self, button):
        self.run_dialog(PaymentMethodsDialog, self.conn)

    def on_devices_setup_activate(self, button):
        self.run_dialog(DeviceSettingsDialog, self.conn)

    def on_tax_constants__activate(self, action):
        self.run_dialog(SellableTaxConstantsDialog, self.conn)
