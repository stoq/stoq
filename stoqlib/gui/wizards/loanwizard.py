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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Loan wizard"""

import gtk

from decimal import Decimal
import datetime

from kiwi.datatypes import ValidationError, currency
from kiwi.python import Settable
from kiwi.ui.widgets.entry import ProxyEntry
from kiwi.ui.objectlist import Column, SearchColumn

from stoqlib.api import api
from stoqlib.database.orm import ORMObjectQueryExecuter
from stoqlib.domain.interfaces import IStorable, ISalesPerson
from stoqlib.domain.person import (ClientView, PersonAdaptToUser,
                                   ClientCategory)
from stoqlib.domain.loan import Loan, LoanItem
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.sale import Sale
from stoqlib.domain.views import LoanView, ProductFullStockItemView
from stoqlib.lib.message import info, yesno
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.formatters import format_quantity, get_formatted_cost
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.search import StoqlibSearchSlaveDelegate
from stoqlib.gui.base.wizards import (WizardEditorStep, BaseWizard,
                                      BaseWizardStep)
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.editors.loaneditor import LoanItemEditor
from stoqlib.gui.printing import print_report
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.gui.wizards.salequotewizard import SaleQuoteItemStep
from stoqlib.reporting.loanreceipt import LoanReceipt

_ = stoqlib_gettext


#
# Wizard Steps
#


class StartNewLoanStep(WizardEditorStep):
    gladefile = 'SalesPersonStep'
    model_type = Loan
    proxy_widgets = ['client', 'salesperson', 'expire_date',
                     'client_category']

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

        self._fill_clients_combo()
        self._fill_clients_category_combo()

        self.expire_date.set_property('mandatory', True)

        # CFOP combo
        self.cfop_lbl.hide()
        self.cfop.hide()
        self.create_cfop.hide()

        # Transporter/RemovedBy Combo
        self.transporter_lbl.set_text(_(u'Removed By:'))
        self.create_transporter.hide()

        # removed_by widget
        self.removed_by = ProxyEntry(unicode)
        self.removed_by.set_property('model-attribute', 'removed_by')
        if 'removed_by' not in self.proxy_widgets:
            self.proxy_widgets.append('removed_by')
        self.removed_by.show()
        self._replace_widget(self.transporter, self.removed_by)

        # Operation Nature widget
        self.operation_nature.hide()
        self.nature_lbl.hide()

    def _fill_clients_combo(self):
        clients = ClientView.get_active_clients(self.conn)
        max_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        clients = clients[:max_results]
        items = [(c.name, c.client) for c in clients]
        self.client.prefill(sorted(items))
        self.client.set_property('mandatory', True)

    def _fill_clients_category_combo(self):
        cats = ClientCategory.select(connection=self.conn).orderBy('name')
        items = [(c.get_description(), c) for c in cats]
        items.insert(0, ['', None])
        self.client_category.prefill(items)

    def _replace_widget(self, old_widget, new_widget):
        # retrieve the position, since we will replace two widgets later.
        parent = old_widget.get_parent()
        top = parent.child_get_property(old_widget, 'top-attach')
        bottom = parent.child_get_property(old_widget, 'bottom-attach')
        left = parent.child_get_property(old_widget, 'left-attach')
        right = parent.child_get_property(old_widget, 'right-attach')
        parent.remove(old_widget)
        parent.attach(new_widget, left, right, top, bottom)
        parent.child_set_property(new_widget, 'y-padding', 3)
        parent.child_set_property(new_widget, 'x-padding', 3)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.toogle_client_details()
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

    def toogle_client_details(self):
        client = self.client.read()
        self.client_details.set_sensitive(bool(client))

    #
    #   Callbacks
    #

    def on_create_client__clicked(self, button):
        trans = api.new_transaction()
        client = run_person_role_dialog(ClientEditor, self.wizard, trans, None)
        retval = api.finish_transaction(trans, client)
        client = self.conn.get(client)
        trans.close()
        if not retval:
            return
        self._fill_clients_combo()
        self.client.select(client)

    def on_client__changed(self, widget):
        self.toogle_client_details()
        client = self.client.get_selected()
        if not client:
            return
        self.client_category.select(client.category)

    def on_expire_date__validate(self, widget, value):
        if value < datetime.date.today():
            msg = _(u"The expire date must be set to today or a future date.")
            return ValidationError(msg)

    def on_notes_button__clicked(self, *args):
        run_dialog(NoteEditor, self.wizard, self.conn, self.model, 'notes',
                   title=_("Additional Information"))

    def on_client_details__clicked(self, button):
        client = self.model.client
        run_dialog(ClientDetailsDialog, self.wizard, self.conn, client)


class LoanItemStep(SaleQuoteItemStep):
    """ Wizard step for loan items selection """
    model_type = Loan
    item_table = LoanItem
    sellable_view = ProductFullStockItemView

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

        sellable = self.proxy.model.sellable
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
        return [SearchColumn('id', title=_('#'), sorted=True,
                             data_type=int, width=80),
                SearchColumn('responsible_name', title=_(u'Responsible'),
                             data_type=str, expand=True),
                SearchColumn('client_name', title=_(u'Client'),
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
        loan = Loan.get(self.search.results.get_selected().id,
                        connection=self.conn)
        self.wizard.model = loan
        return LoanItemSelectionStep(self.wizard, self, self.conn, loan)

    #
    # Callbacks
    #

    def _on_results_selection_changed(self, widget, selection):
        self._refresh_next()


class LoanItemSelectionStep(BaseWizardStep):
    gladefile = 'LoanItemSelectionStep'

    def __init__(self, wizard, previous, conn, loan):
        self.loan = loan
        BaseWizardStep.__init__(self, conn, wizard, previous)
        self._original_items = {}
        self._setup_widgets()

    def _setup_widgets(self):
        self.loan_items.set_columns(self.get_columns())
        self.loan_items.add_list(self.get_saved_items())
        self.edit_button.set_sensitive(False)

    def _validate_step(self, value):
        self.wizard.refresh_next(value)

    def _edit_item(self, item):
        trans = api.new_transaction()
        model = trans.get(item)
        retval = run_dialog(LoanItemEditor, self.wizard, trans, model,
                            expanded_edition=True)
        retval = api.finish_transaction(trans, retval)
        if retval:
            self.loan_items.update(item)
            self._validate_step(True)
        trans.close()

    def _create_sale(self, sale_items):
        user = api.get_current_user(self.conn)
        sale = Sale(connection=self.conn,
                    branch=self.loan.branch,
                    client=self.loan.client,
                    salesperson=ISalesPerson(user.person),
                    cfop=sysparam(self.conn).DEFAULT_SALES_CFOP,
                    group=PaymentGroup(connection=self.conn),
                    coupon_id=None)
        for item, quantity in sale_items:
            sale.add_sellable(item.sellable, price=item.price,
                               quantity=quantity)
        sale.order()
        return sale

    def get_saved_items(self):
        for item in self.loan.get_items():
            self._original_items[item.id] = Settable(item_id=item.id,
                                 sale_qty=item.sale_quantity or Decimal(0),
                                 return_qty=item.return_quantity or Decimal(0))
            yield item

    def get_columns(self):
        return [
            Column('id', title=_('# '), width=60, data_type=str,
                   sorted=True),
            Column('sellable.code', title=_('Code'), width=70, data_type=str),
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True, searchable=True),
            Column('quantity', title=_('Loaned'), data_type=Decimal,
                   format_func=format_quantity),
            Column('sale_quantity', title=_('Sold'), data_type=Decimal,
                   format_func=format_quantity),
            Column('return_quantity', title=_('Returned'), data_type=Decimal,
                   format_func=format_quantity),
            Column('price', title=_('Price'), data_type=currency,
                   format_func=get_formatted_cost)]

    #
    # WizardStep
    #

    def post_init(self):
        self.register_validate_function(self._validate_step)
        self.force_validation()
        self._validate_step(False)
        self.wizard.enable_finish()

    def has_previous_step(self):
        return True

    def has_next_step(self):
        return True

    def next_step(self):
        has_returned = False
        sale_items = []
        for final in self.loan_items:
            initial = self._original_items[final.id]
            sale_quantity = final.sale_quantity - initial.sale_qty
            if sale_quantity > 0:
                sale_items.append((final, sale_quantity))
                # we have to return the product, so it will be available when
                # the user confirm the created sale.
                final.return_product(sale_quantity)

            return_quantity = final.return_quantity - initial.return_qty
            if return_quantity > 0:
                final.return_product(return_quantity)
                if not has_returned:
                    has_returned = True

        msg = ''
        if sale_items:
            self._create_sale(sale_items)
            msg = _(u'A sale was created from loan items. You can confirm '
                     'the sale in the Till application.')
        if has_returned:
            msg += _(u'\nSome products have returned to stock. You can '
                    'check the stock of the items in the Stock application.')
        if sale_items or has_returned:
            info(_(u'Close loan details...'), msg)
            self.wizard.finish()

    #
    # Kiwi Callbacks
    #

    def on_loan_items__selection_changed(self, widget, item):
        self.edit_button.set_sensitive(bool(item))

    def on_loan_items__row_activated(self, widget, item):
        self._edit_item(item)

    def on_edit_button__clicked(self, widget):
        item = self.loan_items.get_selected()
        self._edit_item(item)


#
# Main wizard
#


class NewLoanWizard(BaseWizard):
    size = (775, 400)
    help_section = 'loan'

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
        loan = Loan(responsible=api.get_current_user(conn),
                    branch=api.get_current_branch(conn),
                    connection=conn)
        # Temporarily save the client_category, so it works fine with
        # SaleQuoteItemStep
        loan.client_category = None
        return loan

    def _print_receipt(self, order):
        # we can only print the receipt if the loan was confirmed.
        if yesno(_('Would you like to print the receipt now?'),
                 gtk.RESPONSE_YES, _("Print receipt"), _("Don't print")):
            print_report(LoanReceipt, order)

    #
    # WizardStep hooks
    #

    def finish(self):
        branch = self.model.branch
        for item in self.model.get_items():
            item.do_loan(branch)
        self.retval = self.model
        self.close()
        self._print_receipt(self.model)


class CloseLoanWizard(BaseWizard):
    size = (775, 400)
    title = _(u'Close Loan Wizard')
    help_section = 'loan'

    def __init__(self, conn):
        first_step = LoanSelectionStep(self, conn)
        BaseWizard.__init__(self, conn, first_step, model=None,
                            title=self.title, edit_mode=False)

    #
    # WizardStep hooks
    #

    def finish(self):
        if self.model.can_close():
            self.model.close()
        self.retval = self.model
        self.close()
