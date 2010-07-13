# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
## Author(s):   George Y. Kussumoto                <george@async.com.br>
##
##
""" Loan wizard"""

from decimal import Decimal
import datetime

from kiwi.datatypes import ValidationError
from kiwi.ui.objectlist import SearchColumn

from stoqlib.database.orm import ORMObjectQueryExecuter
from stoqlib.database.runtime import (get_current_branch, get_current_user,
                                      new_transaction, finish_transaction)
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.person import ClientView, PersonAdaptToUser
from stoqlib.domain.loan import Loan, LoanItem
from stoqlib.domain.views import LoanView
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.search import StoqlibSearchSlaveDelegate
from stoqlib.gui.base.wizards import (WizardEditorStep, BaseWizard,
                                      BaseWizardStep)
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.editors.loaneditor import LoanItemEditor
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.gui.wizards.salequotewizard import SaleQuoteItemStep

_ = stoqlib_gettext


#
# Wizard Steps
#


class StartNewLoanStep(WizardEditorStep):
    gladefile = 'SalesPersonStep'
    model_type = Loan
    proxy_widgets = ('client', 'salesperson', 'expire_date')
    cfop_widgets = ('cfop',)

    def _setup_widgets(self):
        # Hide total and subtotal
        self.table1.hide()
        self.hbox4.hide()
        # Hide invoice number details
        self.invoice_number_label.hide()
        self.invoice_number.hide()
        # Responsible combo
        self.salesperson_lbl.set_text(_(u'Responsible:'))
        self.salesperson.set_property('model-attribute', 'responsible')
        users = PersonAdaptToUser.selectBy(is_active=True, connection=self.conn)
        items = [(u.person.name, u) for u in users]
        self.salesperson.prefill(items)
        self.salesperson.set_sensitive(False)
        # Clients combo
        clients = ClientView.get_active_clients(self.conn)
        max_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        clients = clients[:max_results]
        items = [(c.name, c.client) for c in clients]
        self.client.prefill(sorted(items))
        self.client.set_property('mandatory', True)
        # CFOP combo
        self.cfop_lbl.hide()
        self.cfop.hide()
        self.create_cfop.hide()

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        return LoanItemStep(self.wizard, self, self.conn, self.model)

    def has_previous_step(self):
        return False

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    StartNewLoanStep.proxy_widgets)

    #
    #   Callbacks
    #

    def on_create_client__clicked(self, button):
        trans = new_transaction()
        client = run_person_role_dialog(ClientEditor, self, trans, None)
        if not finish_transaction(trans, client):
            return
        if len(self.client) == 0:
            self._fill_clients_combo()
        else:
            self.client.append_item(client.person.name, client)
        self.client.select(client)

    def on_expire_date__validate(self, widget, value):
        if value < datetime.date.today():
            msg = _(u"The expire date must be set to today or a future date.")
            return ValidationError(msg)

    def on_notes_button__clicked(self, *args):
        run_dialog(NoteEditor, self.wizard, self.conn, self.model, 'notes',
                   title=_("Additional Information"))


class LoanItemStep(SaleQuoteItemStep):
    """ Wizard step for loan items selection """
    model_type = Loan
    item_table = LoanItem

    def post_init(self):
        SaleQuoteItemStep.post_init(self)
        self.slave.set_editor(LoanItemEditor)

    def _has_stock(self, sellable, quantity):
        storable = IStorable(sellable.product, None)
        if storable is not None:
            balance = storable.get_full_balance(self.model.branch)
        else:
            balance = Decimal(0)
        return balance >= quantity

    def on_quantity__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'Quantity should be positive.'))

        sellable = self.sellable.get_selected()
        if not self._has_stock(sellable, value):
            return ValidationError(
                _(u'The quantity is greater than the quantity in stock.'))


class LoanSelectionStep(BaseWizardStep):
    gladefile = 'HolderTemplate'

    def __init__(self, wizard, conn):
        BaseWizardStep.__init__(self, conn, wizard)
        self.setup_slaves()

    def _create_filters(self):
        self.search.set_text_field_columns(['client_name'])

    def _get_columns(self):
        return [SearchColumn('id', title=_(u'Number'), sorted=True,
                             data_type=str, width=80),
                SearchColumn('responsible_name', title=_(u'Responsible'),
                             data_type=str, expand=True),
                SearchColumn('client_name', title=_(u'Name'),
                             data_type=str, expand=True),
                SearchColumn('open_date', title=_(u'Opened'),
                             data_type=datetime.date),
                SearchColumn('expire_date', title=_(u'Expire'),
                             data_type=datetime.date),
                SearchColumn('loaned', title=_(u'Loaned'),
                             data_type=Decimal),
        ]

    def _refresh_next(self, value=None):
        has_selected = self.search.results.get_selected() is not None
        self.wizard.refresh_next(has_selected)

    def get_extra_query(self, states):
        return LoanView.q.status == Loan.STATUS_OPEN

    def setup_slaves(self):
        self.search = StoqlibSearchSlaveDelegate(self._get_columns(),
                                        restore_name=self.__class__.__name__)
        self.search.enable_advanced_search()
        self.attach_slave('place_holder', self.search)
        self.executer = ORMObjectQueryExecuter()
        self.search.set_query_executer(self.executer)
        self.executer.set_table(LoanView)
        self.executer.add_query_callback(self.get_extra_query)
        self._create_filters()
        self.search.results.connect('selection-changed',
                                    self._on_results_selection_changed)
        self.search.focus_search_entry()

    #
    # WizardStep
    #

    def has_previous_step(self):
        return False

    def post_init(self):
        self.register_validate_function(self._refresh_next)
        self.force_validation()

    def next_step(self):
        pass

    #
    # Callbacks
    #

    def _on_results_selection_changed(self, widget, selection):
        self._refresh_next()

#
# Main wizard
#


class NewLoanWizard(BaseWizard):
    size = (775, 400)

    def __init__(self, conn, model=None):
        title = self._get_title(model)
        model = model or self._create_model(conn)
        if model.status != Loan.STATUS_OPEN:
            raise ValueError('Invalid loan status. It should '
                             'be STATUS_OPEN')

        first_step = StartNewLoanStep(conn, self, model)
        BaseWizard.__init__(self, conn, first_step, model, title=title,
                            edit_mode=False)

    def _get_title(self, model=None):
        if not model:
            return _('New Loan Wizard')

    def _create_model(self, conn):
        return Loan(responsible=get_current_user(conn),
                    branch=get_current_branch(conn),
                    connection=conn)

    #
    # WizardStep hooks
    #

    def finish(self):
        branch = self.model.branch
        for item in self.model.get_items():
            item.do_loan(branch)
        self.retval = self.model
        self.close()


# select loan
# set quantities
# create sales, close or return

class CloseLoanWizard(BaseWizard):
    size = (775, 400)

    def __init__(self, conn):
        title = self._get_title()
        first_step = LoanSelectionStep(self, conn)
        BaseWizard.__init__(self, conn, first_step, model=None, title=title,
                            edit_mode=False)

    def _get_title(self):
        return _('Close Loan Wizard')

    #
    # WizardStep hooks
    #

    def finish(self):
        self.retval = False
        self.close()
