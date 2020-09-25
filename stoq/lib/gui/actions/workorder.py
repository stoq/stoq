# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Copyright (C) 2018 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#


from gi.repository import Gtk

from stoqlib.api import api
from stoqlib.domain.workorder import WorkOrder
from stoq.lib.gui.actions.base import BaseActions, action
from stoq.lib.gui.editors.noteeditor import NoteEditor, Note
from stoq.lib.gui.editors.workordereditor import (WorkOrderEditor,
                                                  WorkOrderPackageSendEditor,
                                                  WorkOrderCheckEditor)
from stoq.lib.gui.utils.printing import print_report
from stoq.lib.gui.wizards.workorderpackagewizard import WorkOrderPackageReceiveWizard
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.workorder import (WorkOrderReceiptReport,
                                         WorkOrderQuoteReport)

_ = stoqlib_gettext


class WorkOrderActions(BaseActions):

    group_name = 'work_order'

    reopen_question = _("This will reopen the order. Are you sure?")
    cancel_question = _("This will cancel the selected order. Any reserved items "
                        "will return to stock. Are you sure?")
    waiting_question = _("This will inform the order that we are waiting. Are you sure?")
    inform_question = _("How the client was informed?")
    uninform_question = _("This will set the order as uninformed. Are you sure?")

    def model_set(self, model):
        if model and model.sale is not None:
            has_quote = model.order_items.count() > 0
        else:
            has_quote = model and bool(model.defect_reported or model.defect_detected)

        branch = model and api.get_current_branch(model.store)
        self.set_action_enabled('Details', model)
        self.set_action_enabled('Edit', model and model.can_edit())
        self.set_action_enabled('Approve', model and model.can_approve())
        self.set_action_enabled('Finish', model and model.can_finish(branch))
        self.set_action_enabled('Close', model and model.can_close(branch))
        self.set_action_enabled('Cancel', model and model.can_cancel())
        self.set_action_enabled('Reject', model and model.can_reject()),
        self.set_action_enabled('UndoRejection', model and model.can_undo_rejection())
        self.set_action_enabled('Pause', model and model.can_pause())
        self.set_action_enabled('Work', model and model.can_work(branch))
        self.set_action_enabled('CheckOrder', model and model.can_check_order()),
        self.set_action_enabled('InformClient', model and model.can_inform_client())
        self.set_action_enabled('Reopen', model and model.can_reopen())
        self.set_action_enabled('PrintReceipt', model and model.is_finished())
        self.set_action_enabled('PrintQuote', bool(has_quote))
        self.set_action_enabled('FinishOrClose', model and (model.can_finish(branch) or
                                                            model.can_close(branch)))

    #
    #   Private
    #

    def _run_notes_editor(self, msg_text=u'', mandatory=True, reason=_('Reason')):
        return self.run_dialog(NoteEditor, None, model=Note(),
                               message_text=msg_text, label_text=reason,
                               mandatory=mandatory)

    #
    #   Actions
    #

    @action('NewOrder', require_model=False)
    def new_order(self, category=None, available_categories=None):
        with api.new_store() as store:
            work_order = self.run_dialog(WorkOrderEditor, store,
                                         category=store.fetch(category),
                                         available_categories=available_categories)

        if store.committed:
            self.emit('model-created', work_order)

    @action('Details')
    def details(self, work_order):
        with api.new_store() as store:
            self.run_dialog(WorkOrderEditor, store,
                            model=store.fetch(work_order),
                            visual_mode=True)

    @action('Edit')
    def edit_order(self, work_order):
        with api.new_store() as store:
            self.run_dialog(WorkOrderEditor, store,
                            model=store.fetch(work_order))

        if store.committed:
            self.emit('model-edited', work_order)

    @action('EditOrDetails')
    def edit_or_details(self, work_order):
        if self.get_action('Edit').get_enabled():
            self.edit_order(work_order)
        else:
            assert self.get_action('Details').get_enabled()
            self.details(work_order)

    @action('Approve')
    def approve_order(self, work_order):
        if not yesno(_("This will inform the order that the client has "
                       "approved the work. Are you sure?"),
                     Gtk.ResponseType.NO, _("Approve"), _("Don't approve")):
            return

        with api.new_store() as store:
            work_order = store.fetch(work_order)
            work_order.approve()

        self.emit('model-edited', work_order)

    @action('FinishOrClose')
    def finish_or_deliver_order(self, work_order):
        if work_order.status == WorkOrder.STATUS_WORK_FINISHED:
            self.close_order(work_order)
        else:
            self.finish_order(work_order)

    @action('Finish')
    def finish_order(self, work_order):
        if work_order.is_items_totally_reserved():
            msg = _("This will finish the selected order, marking the "
                    "work as done. Are you sure?")
        else:
            msg = _("Some items on this work order are not fully reserved. "
                    "Do you still want to mark it as finished?")

        if not yesno(msg, Gtk.ResponseType.NO,
                     _("Finish order"), _("Don't finish")):
            return

        with api.new_store() as store:
            work_order = store.fetch(work_order)
            work_order.finish(api.get_current_branch(store), api.get_current_user(store))

        self.emit('model-edited', work_order)

    @action('Cancel')
    def cancel_order(self, work_order):
        rv = self._run_notes_editor(msg_text=self.cancel_question)
        if not rv:
            return

        with api.new_store() as store:
            work_order = store.fetch(work_order)
            work_order.cancel(api.get_current_user(store), reason=rv.notes)
        self.emit('model-edited', work_order)

    @action('Close')
    def close_order(self, work_order):
        if not yesno(_("This will mark the order as delivered. Are you "
                       "sure?"),
                     Gtk.ResponseType.NO, _("Mark as delivered"),
                     _("Don't mark")):
            return

        with api.new_store() as store:
            work_order = store.fetch(work_order)
            work_order.close()

        self.emit('model-edited', work_order)

    @action('Pause')
    def pause_order(self, work_order):
        rv = self._run_notes_editor(msg_text=self.waiting_question)
        if not rv:
            return

        with api.new_store() as store:
            work_order = store.fetch(work_order)
            work_order.pause(reason=rv.notes)

        self.emit('model-edited', work_order)

    @action('Work')
    def work(self, work_order):
        with api.new_store() as store:
            work_order = store.fetch(work_order)
            work_order.work()

        self.emit('model-edited', work_order)

    @action('Reject')
    def reject(self, work_order):
        msg_text = _("This will reject the order. Are you sure?")
        rv = self._run_notes_editor(msg_text=msg_text)
        if not rv:
            return

        with api.new_store() as store:
            work_order = store.fetch(work_order)
            work_order.reject(reason=rv.notes)

        self.emit('model-edited', work_order)

    @action('CheckOrder')
    def check_order(self, work_order):
        with api.new_store() as store:
            rv = self.run_dialog(WorkOrderCheckEditor, store)
            if not rv:
                return

            work_order = store.fetch(work_order)
            work_order.check_order(rv.responsible, rv.notes)

        self.emit('model-edited', work_order)

    @action('InformClient')
    def inform_client(self, work_order):
        rv = self._run_notes_editor(reason=self.inform_question)
        if not rv:
            return

        with api.new_store() as store:
            work_order = store.fetch(work_order)
            # Make the work_order go through all the status
            if not work_order.is_finished():
                work_order.change_status(WorkOrder.STATUS_WORK_FINISHED)

            work_order.inform_client(rv.notes)

        self.emit('model-edited', work_order)

    @action('UndoRejection')
    def undo_rejection(self, work_order):
        msg_text = _("This will undo the rejection of the order. "
                     "Are you sure?")
        rv = self._run_notes_editor(msg_text=msg_text, mandatory=False)
        if not rv:
            return

        with api.new_store() as store:
            work_order = store.fetch(work_order)
            work_order.undo_rejection(reason=rv.notes)

        self.emit('model-edited', work_order)

    @action('Reopen')
    def reopen(self, work_order):
        rv = self._run_notes_editor(msg_text=self.reopen_question)
        if not rv:
            return

        with api.new_store() as store:
            work_order = store.fetch(work_order)
            work_order.reopen(reason=rv.notes)

        self.emit('model-edited', work_order)

    @action('PrintQuote')
    def print_quote(self, work_order):
        print_report(WorkOrderQuoteReport, work_order)

    @action('PrintReceipt')
    def print_receipt(self, work_order):
        print_report(WorkOrderReceiptReport, work_order)

    @action('SendOrders')
    def send_orders(self, work_order):
        with api.new_store() as store:
            self.run_dialog(WorkOrderPackageSendEditor, store)

        if store.committed:
            self.emit('model-edited', None)

    @action('ReceiveOrders')
    def receive_orders(self, work_order):
        with api.new_store() as store:
            self.run_dialog(WorkOrderPackageReceiveWizard, store)

        if store.committed:
            self.emit('model-edited', None)
