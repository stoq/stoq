# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2012 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Events used in the domain code
"""

from stoqlib.lib.decorators import public
from stoqlib.lib.event import Event


#
# Application events
#

@public(since="1.5.0")
class StartApplicationEvent(Event):
    """Emitted when an application is activated

    :param appname: the name of the application
    :param app: the app itself
    """


@public(since="1.5.0")
class StopApplicationEvent(Event):
    """Emitted when an application is deactivated

    :param appname: the name of the application
    :param app: the app itself
    """


class ApplicationSetupSearchEvent(Event):
    """Emitted when a search slave is created.

    :param dialog: The application that is being prepared for search.
    """


#
# Dialog events
#

class RunDialogEvent(Event):
    """This is emitted when a dialog is about to be run.

    This event gives the opportunity to change the dialog that is being displayed
    for another one.

    For instance, a plugin could change the product editor for a more
    specialized one, or could change the sale wizard for another one that has a
    slightly different process.

    This event is emitted with the same arguments that were passed to
    :func:`stoqlib.gui.base.run_dialog`

    If the return value is not ``None``, it should be a new dialog to replace the
    one that would be run. Note that the new dialog should be prepared to handle
    the same arguments as the original dialog.

    :param dialog: The dialog that will be run
    :param parent: The parent of the dialog
    :param args: Custom positional arguments
    :param kwargs: Custom keyword arguments.
    :retval: The new dialog to be displayed, or the original dialog, if no one
      handled this event
    """

    @classmethod
    def emit(cls, dialog, parent, *args, **kwargs):
        retval = super(RunDialogEvent, cls).emit(dialog, parent, *args, **kwargs)
        # When nobody catches the event, lets return the default dialog
        if retval is None:
            return dialog
        return retval


class DialogCreateEvent(Event):
    """Emitted when a dialog is instantiated

    :param dialog: an instance of :class:`stoqlib.gui.base.dialogs.BasicDialog`
    """


@public(since="1.8.0")
class EditorCreateEvent(Event):
    """Emitted when an editor is instantiated.

    Note that since a BaseEditor is also a BaseEditorSlave, the
    EditorSlaveCreateEvent will also be emitted. The main difference from this
    event to the other one, is that when this event is emitted, the editor
    already has a main_window property that can be used.

    :param editor: a subclass of
        :class:`stoqlib.gui.editor.baseeditor.BaseEditor`
    :param model: usually a subclass of :class:`stoqlib.domain.base.Domain`
    :param store: the database store used in editor and model
    :param visual_mode: a bool defining if the editor was created
        on visual_mode.
    """


@public(since="1.7.0")
class EditorSlaveCreateEvent(Event):
    """Emitted when a slave editor is instantiated

    :param editor: a subclass of
        :class:`stoqlib.gui.editor.baseeditor.BaseEditorSlave`
    :param model: usually a subclass of :class:`stoqlib.domain.base.Domain`
    :param store: the database store used in editor and model
    :param visual_mode: a bool defining if the editor was created
        on visual_mode.
    """


@public(since="1.8.0")
class EditorSlaveConfirmEvent(Event):
    """Emitted when a slave editor is confirmed

    :param editor: a subclass of
        :class:`stoqlib.gui.editor.baseeditor.BaseEditorSlave`
    :param model: usually a subclass of :class:`stoqlib.domain.base.Domain`
    :param store: the database store used in editor and model
    :param visual_mode: a bool defining if the editor was created
        on visual_mode.
    """


class SearchDialogSetupSearchEvent(Event):
    """Emitted when a search slave is created.

    :param dialog: The dialog that is being prepared for search.
    """


#
#  Printing events
#

@public(since="1.8.0")
class PrintReportEvent(Event):
    """Emitted when a report is going to be printed

    Useful if the report is going to be replaced by another. In that
    case, the callback connected to this event should return ``True``
    and the original printing won't happen.

    :param report_class: the report class
    :param *args: extra args for the report class
    :param **kwargs: extra kwargs for the report class
    """


class SaleQuoteFinishPrintEvent(Event):
    """Emitted when finish a sale quote

    If a callsite return a value from this event, the default report will not be printed.
    :param sale: the sale that will generate a new report
    """


#
#   Searching Events
#

@public(since='1.9.0')
class CanSeeAllBranches(Event):
    """This is emmited when a branch filter is being created and we should
    decide if all branches should be selectable or only the current one.
    """


#
# CouponCreatedEvent
#


class CouponCreatedEvent(Event):
    """Emitted when a coupon is to be created on fiscalprinter.

    :param coupon: The newly created coupon
    :type coupon: :stoqlib.gui.fiscalprinter.FiscalCoupon
    :param sale: The |sale| to wich we are creating the coupon.
        Will be ``None`` when it is still in progress
        (i.e. a sale in progress on POS).
    """


#
# Stock Update Events
#


@public(since="1.5.0")
class WizardSellableItemStepEvent(Event):
    """
    This event is emitted when the `items step <stoqlib.gui.wizard...>` of the
    receiving wizard is reached.

    :param wizard_step: The product receiving order dialog.
    """


#
# POS Events
#


@public(since="1.5.0")
class POSConfirmSaleEvent(Event):
    """
    This event is emitted in case a sale is confirmed in the pos app.

    Note that the `<ConfirmSaleEvent>` is also emitted, right before this event, but
    this event may not be emitted if the sale is being confirmed outside the pos
    app.

    :param sale_items: A list of objects representing the itens added in the
      Sale. This objects are instances of `<stoq.gui.pos.TemporarySaleItem>`
    """


#
# Wizard Events
#


@public(since="1.5.0")
class NewLoanWizardFinishEvent(Event):
    """
    This event is emitted in case a loan is confirmed in the New Loan Wizard.

    :param loan: The `loan <stoqlib.domain.loan.Loan>` object that represents
      the loan created.
    """


@public(since="1.5.0")
class LoanItemSelectionStepEvent(Event):
    """
    This event is emitted in item selection step of the close loan wizard

    :param step: The step itself
    """


@public(since="1.5.0")
class CloseLoanWizardFinishEvent(Event):
    """
    This event is emitted when
    `stoqlib.gui.wizards.loanwizard.CloseLoanWizard>` finishes

    :param loans: A list of all closed |loans|.
    :param created_sale: The |sale| object that was created for the closed loans
    :param wizard: The `stoqlib.gui.wizards.loanwizard.CloseLoanWizard>`
      itself
    """


@public(since="1.5.0")
class ReceivingOrderWizardFinishEvent(Event):
    """
    This event is emitted in case an order is received in the Receiving Order
    Wizard.

    :param order: The `receiving order <stoqlib.domain.receiving.ReceivingOrder>`
      object that represents the order received.
    """


@public(since="1.5.0")
class SaleReturnWizardFinishEvent(Event):
    """
    This event is emitted in case a sale is returned in the Sale Return Wizard.

    :param returned_sale: The `returned sale
      <stoqlib.domain.returned_sale.ReturnedSale>` object that represents the
      sale returned.
    """


@public(since="1.5.0")
class SaleTradeWizardFinishEvent(Event):
    """
    This event is emitted in case a new trade is created in the Sale Trade
    Wizard. Note that the trade will only be confirmed after the new sale is
    confirmed in the POS app.

    :param returned_sale: The `returned sale
      <stoqlib.domain.returnedsale.ReturnedSale>` object that represents the
      sale returned.
    """


@public(since="1.5.0")
class StockDecreaseWizardFinishEvent(Event):
    """
    This event is emitted in case the stock is decreased in the Stock Decrease
    Wizard.

    :param stock_decreased: The `stock decrease
      <stoqlib.domain.stockdecrease.StockDecrease>` object that represents the
      stock decrement.
    """


@public(since="1.5.0")
class StockTransferWizardFinishEvent(Event):
    """
    This event is emitted in case a stock transfer is ordered in the Stock
    Transfer Wizard.

    :param transfer_order: The `transfer order
      <stoqlib.domain.transfer.TransferOrder>` object that represents the stock
      transfer.
    """


@public(since="1.8.0")
class ConfirmSaleWizardFinishEvent(Event):
    """
    This event is emitted in case a sale is confirmed using the confirm sale
    wizard

    :param sale: The |sale| that was confirmed.
    """


@public(since="1.8.0")
class SaleQuoteWizardFinishEvent(Event):
    """
    This event is emitted in case a sale quote is created using the sale quote
    wizard.

    :param sale: The |sale| that was created.
    """


@public(since="1.10.0")
class ClientSaleValidationEvent(Event):
    """
     This event is issued when the customer is selected in a sale wizard.

     :param person: The person
        <stoqlib.domain.person.Person> object to extract the street number.
    """
